"""
企業ごとに格納されたXBRLファイルを処理して、抽出結果を保存するスクリプト
"""

from datetime import datetime
from itertools import islice, tee, filterfalse
import json
import logging.handlers
from pathlib import Path
import logging
from logging.handlers import QueueHandler, QueueListener
import sys
from typing import Literal, Optional

from pydantic import BaseModel

from extract_financial_statements_from_xbrl import DocumentMetadata
from xbrl_utils import (
    LOGGER_NAME,
    BSInstance,
    PLInstance,
    CFInstance,
    get_bs_concepts,
    get_cf_concepts,
    get_pl_concepts,
    load_edinet_xbrl_model_from_zip,
    get_formatted_fiscal_year,
)
import multiprocessing
from concurrent.futures import ProcessPoolExecutor


RESULT_ROOT_DIR = Path("json-data-v2")
RESULT_ROOT_DIR.mkdir(exist_ok=True)


def construct_result_file_path(company_folder: Path) -> Path:
    edinet_code = company_folder.name
    return RESULT_ROOT_DIR / f"{edinet_code}" / "result.json"


NUM_PROCESSES = 20
XBRL_ARCHIVE_FILES = list(filter(lambda x: x.is_dir(), Path("xbrl-files").glob("*")))
# 20250211.error.log でエラーが出ていたもの
# XBRL_ARCHIVE_FILES = list(
#     map(
#         Path,
#         [
#             "xbrl-files/E00023",
#             "xbrl-files/E00334",
#             "xbrl-files/E00574",
#             "xbrl-files/E00678",
#             "xbrl-files/E00816",
#             "xbrl-files/E01737",
#             "xbrl-files/E01832",
#             "xbrl-files/E02126",
#             "xbrl-files/E02127",
#             "xbrl-files/E02224",
#             "xbrl-files/E02778",
#             "xbrl-files/E03044",
#             "xbrl-files/E03125",
#             "xbrl-files/E03345",  #  # CF root_concept が 1 つではなく、3つ
#             "xbrl-files/E04130",
#             "xbrl-files/E04246",
#             "xbrl-files/E04902",
#             "xbrl-files/E05015",
#             "xbrl-files/E05369",
#             "xbrl-files/E05651",
#             "xbrl-files/E05951",
#             "xbrl-files/E22663",
#             "xbrl-files/E26095",
#             "xbrl-files/E26327",
#             "xbrl-files/E32750",
#             "xbrl-files/E33382",
#             "xbrl-files/E33625",
#             "xbrl-files/E33868",
#             "xbrl-files/E36133",
#             "xbrl-files/E37785",
#         ],
#     )
# )

XBRL_ARCHIVE_FILES = list(
    filterfalse(lambda x: construct_result_file_path(x).exists(), XBRL_ARCHIVE_FILES)
)
# XBRL_ARCHIVE_FILES = list(islice(XBRL_ARCHIVE_FILES, 200))


class FinancialStatementDocument(BaseModel):
    companyName: str
    editnetCode: str
    docID: str
    docType: Literal["Annual", "Quarterly", "SemiAnnual"]
    jcn: Optional[str]
    secCode: Optional[str]
    fiscalYear: Optional[str]
    submittionDate: datetime
    financialYearStartDate: datetime
    financialYearEndDate: datetime
    bs: list[BSInstance]
    cf: list[CFInstance]
    pl: list[PLInstance]
    hasPDF: bool
    hasXBRL: bool
    hasCSV: bool


class AggregatedFinancialStatement(BaseModel):
    # 連結
    consolidatedYearlyProfitAndLossStatements: list[PLInstance]
    consolidatedSemiAnnualProfitAndLossStatements: list[PLInstance]
    consolidatedQuarterlyProfitAndLossStatements: list[PLInstance]
    consolidatedBalanceSheets: list[BSInstance]
    consolidatedYearlyCashFlowStatements: list[CFInstance]
    consolidatedSemiAnnualCashFlowStatements: list[CFInstance]
    consolidatedQuarterlyCashFlowStatements: list[CFInstance]
    # 非連結
    nonConsolidatedYearlyProfitAndLossStatements: list[PLInstance]
    nonConsolidatedSemiAnnualProfitAndLossStatements: list[PLInstance]
    nonConsolidatedQuarterlyProfitAndLossStatements: list[PLInstance]
    nonConsolidatedBalanceSheets: list[BSInstance]
    nonConsolidatedYearlyCashFlowStatements: list[CFInstance]
    nonConsolidatedSemiAnnualCashFlowStatements: list[CFInstance]
    nonConsolidatedQuarterlyCashFlowStatements: list[CFInstance]


class Company(BaseModel):
    name: str
    edinetCode: str
    jcn: Optional[str]
    secCode: Optional[str]
    aggregatedFinancialStatements: AggregatedFinancialStatement

    financialStatementDocuments: list[FinancialStatementDocument]


def load_doc_metadata(xbrl_archive_file: Path) -> DocumentMetadata:
    metadata_file = xbrl_archive_file.with_suffix(".json")
    loaded_data = json.loads(metadata_file.read_text())
    return DocumentMetadata(**loaded_data)


def convert_doc_type_code_to_literal(
    doc_type_code: str,
) -> Literal["Annual", "Quarterly", "SemiAnnual"]:
    if doc_type_code == "120":
        return "Annual"
    elif doc_type_code == "140":
        return "Quarterly"
    elif doc_type_code == "160":
        return "SemiAnnual"
    else:
        raise ValueError(f"Invalid doc_type_code: {doc_type_code}")


def calc_month_duration(from_month: int, to_month: int) -> int:
    """
    3 -> 6 = 3
    12 -> 1 = 1
    2 -> 1 = 11
    12 -> 12 = 0
    10 -> 1 = 3
    """
    if from_month == to_month:
        return 0
    if from_month < to_month:
        return to_month - from_month
    return 12 - from_month + to_month


def aggregate_financial_statements(
    financial_statements_documents: list[FinancialStatementDocument],
) -> AggregatedFinancialStatement:
    consolidated_annual_pls: list[PLInstance] = []
    consolidated_semianual_pls: list[PLInstance] = []
    consolidated_quarterly_pls: list[PLInstance] = []
    consolidated_bss: list[BSInstance] = []
    consolidated_annual_fcs: list[CFInstance] = []
    consolidated_semianual_fcs: list[CFInstance] = []
    consolidated_quarterly_fcs: list[CFInstance] = []
    nonconsolidated_annual_pls: list[PLInstance] = []
    nonconsolidated_semianual_pls: list[PLInstance] = []
    nonconsolidated_quarterly_pls: list[PLInstance] = []
    nonconsolidated_bss: list[BSInstance] = []
    nonconsolidated_annual_fcs: list[CFInstance] = []
    nonconsolidated_semianual_fcs: list[CFInstance] = []
    nonconsolidated_quarterly_fcs: list[CFInstance] = []
    for financial_statements in financial_statements_documents:
        # PL
        for pl in financial_statements.pl:
            month_duration = calc_month_duration(
                pl.durationFrom.month, pl.durationTo.month
            )
            if month_duration == 0:
                consolidated_annual_pls.append(
                    pl
                ) if pl.consolidated else nonconsolidated_annual_pls.append(pl)
            elif month_duration == 6:
                consolidated_semianual_pls.append(
                    pl
                ) if pl.consolidated else nonconsolidated_semianual_pls.append(pl)
            elif month_duration == 3 or month_duration == 9:
                consolidated_quarterly_pls.append(
                    pl
                ) if pl.consolidated else nonconsolidated_quarterly_pls.append(pl)

        # BS
        for bs in financial_statements.bs:
            consolidated_bss.append(
                bs
            ) if bs.consolidated else nonconsolidated_bss.append(bs)

        # CF
        for cf in financial_statements.cf:
            month_duration = calc_month_duration(
                cf.durationFrom.month, cf.durationTo.month
            )
            if month_duration == 0:
                consolidated_annual_fcs.append(
                    cf
                ) if cf.consolidated else nonconsolidated_annual_fcs.append(cf)
            elif month_duration == 6:
                consolidated_semianual_fcs.append(
                    cf
                ) if cf.consolidated else nonconsolidated_semianual_fcs.append(cf)
            elif month_duration == 3 or month_duration == 9:
                consolidated_quarterly_fcs.append(
                    cf
                ) if cf.consolidated else nonconsolidated_quarterly_fcs.append(cf)

    def pl_key(pl: PLInstance) -> str:
        return f"{pl.durationFrom}_{pl.durationTo}"

    def deduplicate_pl_with_selecting_original_doc(
        pls: list[PLInstance],
    ) -> list[PLInstance]:
        deduplicated_pls_dict: dict[str, PLInstance] = {}
        for pl in pls:
            if pl_key(pl) not in deduplicated_pls_dict:
                deduplicated_pls_dict[pl_key(pl)] = pl
            else:
                # docSubmissionDateが古いほうを選択
                new_pl = pl
                old_pl = deduplicated_pls_dict[pl_key(pl)]
                if new_pl.docSubmissionDate < old_pl.docSubmissionDate:
                    deduplicated_pls_dict[pl_key(pl)] = pl

        deduplicated_pls = list(deduplicated_pls_dict.values())
        deduplicated_pls = sorted(deduplicated_pls, key=lambda pl: pl.durationFrom)
        return deduplicated_pls

    consolidated_annual_pls = deduplicate_pl_with_selecting_original_doc(
        consolidated_annual_pls
    )
    consolidated_semianual_pls = deduplicate_pl_with_selecting_original_doc(
        consolidated_semianual_pls
    )
    consolidated_quarterly_pls = deduplicate_pl_with_selecting_original_doc(
        consolidated_quarterly_pls
    )
    nonconsolidated_annual_pls = deduplicate_pl_with_selecting_original_doc(
        nonconsolidated_annual_pls
    )
    nonconsolidated_semianual_pls = deduplicate_pl_with_selecting_original_doc(
        nonconsolidated_semianual_pls
    )
    nonconsolidated_quarterly_pls = deduplicate_pl_with_selecting_original_doc(
        nonconsolidated_quarterly_pls
    )

    def bs_key(bs: BSInstance) -> str:
        return bs.period

    def deduplicate_bs_with_selecting_original_doc(
        bss: list[BSInstance],
    ) -> list[BSInstance]:
        deduplicated_bss_dict: dict[str, BSInstance] = {}
        for bs in bss:
            if bs_key(bs) not in deduplicated_bss_dict:
                deduplicated_bss_dict[bs_key(bs)] = bs
            else:
                # docSubmissionDateが古いほうを選択
                new_bs = bs
                old_bs = deduplicated_bss_dict[bs_key(bs)]
                if new_bs.docSubmissionDate < old_bs.docSubmissionDate:
                    deduplicated_bss_dict[bs_key(bs)] = bs

        deduplicated_bss = list(deduplicated_bss_dict.values())
        deduplicated_bss = sorted(deduplicated_bss, key=lambda bs: bs.period)
        return deduplicated_bss

    consolidated_bss = deduplicate_bs_with_selecting_original_doc(consolidated_bss)
    nonconsolidated_bss = deduplicate_bs_with_selecting_original_doc(
        nonconsolidated_bss
    )

    def cf_key(cf: CFInstance) -> str:
        return f"{cf.durationFrom}_{cf.durationTo}"

    def deduplicate_cf_with_selecting_original_doc(
        fcs: list[CFInstance],
    ) -> list[CFInstance]:
        deduplicated_fcs_dict: dict[str, CFInstance] = {}
        for cf in fcs:
            if cf_key(cf) not in deduplicated_fcs_dict:
                deduplicated_fcs_dict[cf_key(cf)] = cf
            else:
                # docSubmissionDateが古いほうを選択
                new_cf = cf
                old_cf = deduplicated_fcs_dict[cf_key(cf)]
                if new_cf.docSubmissionDate < old_cf.docSubmissionDate:
                    deduplicated_fcs_dict[cf_key(cf)] = cf

        deduplicated_fcs = list(deduplicated_fcs_dict.values())
        deduplicated_fcs = sorted(deduplicated_fcs, key=lambda cf: cf.durationFrom)
        return deduplicated_fcs

    consolidated_annual_fcs = deduplicate_cf_with_selecting_original_doc(
        consolidated_annual_fcs
    )
    consolidated_semianual_fcs = deduplicate_cf_with_selecting_original_doc(
        consolidated_semianual_fcs
    )
    consolidated_quarterly_fcs = deduplicate_cf_with_selecting_original_doc(
        consolidated_quarterly_fcs
    )
    nonconsolidated_annual_fcs = deduplicate_cf_with_selecting_original_doc(
        nonconsolidated_annual_fcs
    )
    nonconsolidated_semianual_fcs = deduplicate_cf_with_selecting_original_doc(
        nonconsolidated_semianual_fcs
    )
    nonconsolidated_quarterly_fcs = deduplicate_cf_with_selecting_original_doc(
        nonconsolidated_quarterly_fcs
    )

    return AggregatedFinancialStatement(
        consolidatedYearlyProfitAndLossStatements=consolidated_annual_pls,
        consolidatedSemiAnnualProfitAndLossStatements=consolidated_semianual_pls,
        consolidatedQuarterlyProfitAndLossStatements=consolidated_quarterly_pls,
        consolidatedBalanceSheets=consolidated_bss,
        consolidatedYearlyCashFlowStatements=consolidated_annual_fcs,
        consolidatedSemiAnnualCashFlowStatements=consolidated_semianual_fcs,
        consolidatedQuarterlyCashFlowStatements=consolidated_quarterly_fcs,
        nonConsolidatedYearlyProfitAndLossStatements=nonconsolidated_annual_pls,
        nonConsolidatedSemiAnnualProfitAndLossStatements=nonconsolidated_semianual_pls,
        nonConsolidatedQuarterlyProfitAndLossStatements=nonconsolidated_quarterly_pls,
        nonConsolidatedBalanceSheets=nonconsolidated_bss,
        nonConsolidatedYearlyCashFlowStatements=nonconsolidated_annual_fcs,
        nonConsolidatedSemiAnnualCashFlowStatements=nonconsolidated_semianual_fcs,
        nonConsolidatedQuarterlyCashFlowStatements=nonconsolidated_quarterly_fcs,
    )


def process_company_folder(
    company_folder: Path,
    current_task_num: int,
    total_task_num: int,
    log_queue: multiprocessing.Queue,
) -> None:
    logger = logging.getLogger(company_folder.name)
    handler = QueueHandler(log_queue)
    logger.handlers.clear()
    logger.addHandler(handler)

    formatter = logging.Formatter(f"[{current_task_num}/{total_task_num}] %(message)s")
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    utils_logger = logging.getLogger(LOGGER_NAME)
    utils_logger.parent = logger

    logger.info(f"{company_folder}")

    company_financial_statements: list[FinancialStatementDocument] = []

    try:
        XBRL_ARCHIVE_FILES = company_folder.glob("**/*_xbrl.zip")
        _files_for_total_count, XBRL_ARCHIVE_FILES = tee(XBRL_ARCHIVE_FILES)
        total_file_count = len(list(_files_for_total_count))
        for current_file_num, xbrl_archive_file in enumerate(XBRL_ARCHIVE_FILES, 1):
            try:
                logger.info(
                    f"[{current_file_num}/{total_file_count}]: start {xbrl_archive_file}"
                )
                xbrl_model, cntlr = load_edinet_xbrl_model_from_zip(xbrl_archive_file)

                document_metadata = load_doc_metadata(
                    xbrl_archive_file.parent / "metadata.json"
                )
                submittion_date = datetime.strptime(
                    document_metadata.submitDateTime, "%Y-%m-%d %H:%M"
                )
                fiscal_year_start_date = datetime.strptime(
                    document_metadata.periodStart, "%Y-%m-%d"
                )
                fiscal_year_end_date = datetime.strptime(
                    document_metadata.periodEnd, "%Y-%m-%d"
                )
                formatted_fiscal_year = get_formatted_fiscal_year(xbrl_model)
                doc_type = convert_doc_type_code_to_literal(
                    document_metadata.docTypeCode
                )

                bs_concepts = get_bs_concepts(
                    xbrl_model,
                    doc_id=document_metadata.docID,
                    doc_type=doc_type,
                    doc_submission_date=submittion_date,
                )
                logger.info(f"Got {len(bs_concepts)} BS concepts")
                cf_concepts = get_cf_concepts(
                    xbrl_model,
                    doc_id=document_metadata.docID,
                    doc_type=doc_type,
                    doc_submission_date=submittion_date,
                )
                logger.info(f"Got {len(cf_concepts)} CF concepts")
                pl_concepts = get_pl_concepts(
                    xbrl_model,
                    doc_id=document_metadata.docID,
                    doc_type=doc_type,
                    doc_submission_date=submittion_date,
                )
                logger.info(f"Got {len(pl_concepts)} PL concepts")

                bs_instances: list[BSInstance] = []
                for bs_concept in bs_concepts:
                    extracted_bs_instances = bs_concept.extract_instances()
                    bs_instances.extend(extracted_bs_instances)
                logger.info(f"Extracted {len(bs_instances)} BS instances")

                cf_instances: list[CFInstance] = []
                for cf_concept in cf_concepts:
                    extracted_cf_instances = cf_concept.extract_instances()
                    cf_instances.extend(extracted_cf_instances)
                logger.info(f"Extracted {len(cf_instances)} CF instances")

                pl_instances: list[PLInstance] = []
                for pl_concept in pl_concepts:
                    extracted_pl_instances = pl_concept.extract_instances()
                    pl_instances.extend(extracted_pl_instances)
                logger.info(f"Extracted {len(pl_instances)} PL instances")

                financial_statement_document = FinancialStatementDocument(
                    companyName=document_metadata.filerName,
                    editnetCode=document_metadata.edinetCode,
                    secCode=document_metadata.secCode,
                    jcn=document_metadata.JCN,
                    docID=document_metadata.docID,
                    docType=doc_type,
                    fiscalYear=formatted_fiscal_year if formatted_fiscal_year else None,
                    financialYearStartDate=fiscal_year_start_date,
                    financialYearEndDate=fiscal_year_end_date,
                    submittionDate=submittion_date,
                    bs=bs_instances,
                    cf=cf_instances,
                    pl=pl_instances,
                    hasPDF=document_metadata.pdfFlag == "1",
                    hasXBRL=document_metadata.xbrlFlag == "1",
                    hasCSV=document_metadata.csvFlag == "1",
                )
                company_financial_statements.append(financial_statement_document)
            except Exception as e:
                logger.error(
                    f"Error processing archived file {xbrl_archive_file}: {e}\n",
                    exc_info=True,
                )
                break
            finally:
                cntlr.close()

        company_financial_statements = sorted(
            company_financial_statements, key=lambda x: x.submittionDate
        )
        if len(company_financial_statements) == 0:
            logger.warning("No financial statements found")
            return

        latest_financial_statement = company_financial_statements[-1]
        logger.info(f"got {len(company_financial_statements)} financial statements")

        aggregated_financial_statements = aggregate_financial_statements(
            company_financial_statements
        )

        company = Company(
            name=latest_financial_statement.companyName,
            edinetCode=latest_financial_statement.editnetCode,
            jcn=latest_financial_statement.jcn,
            secCode=latest_financial_statement.secCode,
            financialStatementDocuments=company_financial_statements,
            aggregatedFinancialStatements=aggregated_financial_statements,
        )

        result_file_path = RESULT_ROOT_DIR / f"{company.edinetCode}" / "result.json"
        json_data = company.model_dump(mode="json")
        result_file_path.parent.mkdir(exist_ok=True, parents=True)
        result_file_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False))

        logger.info(f"Aggregated financial statements are saved to {result_file_path}")

    except Exception as e:
        logger.error(
            f"Error processing company folder {company_folder}: {e}\n", exc_info=True
        )
        return


if __name__ == "__main__":
    total_task_num: int = len(XBRL_ARCHIVE_FILES)

    log_queue = multiprocessing.Manager().Queue()
    default_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(default_formatter)
    console_handler.setLevel(logging.DEBUG)
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setFormatter(default_formatter)
    error_handler.setLevel(logging.WARNING)
    listener = QueueListener(
        log_queue, console_handler, error_handler, respect_handler_level=True
    )
    listener.start()

    try:
        with ProcessPoolExecutor(max_workers=NUM_PROCESSES) as executor:
            futures = [
                executor.submit(
                    process_company_folder,
                    company_folder,
                    current_task_num,
                    total_task_num,
                    log_queue,
                )
                for current_task_num, company_folder in enumerate(XBRL_ARCHIVE_FILES, 1)
            ]
            for future in futures:
                future.result()
    except KeyboardInterrupt:
        print("\nInterrupt received! Stopping processes...")
        executor.shutdown(wait=True, cancel_futures=True)
        sys.exit(0)

    listener.stop()
