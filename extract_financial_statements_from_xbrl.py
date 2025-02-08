from datetime import datetime
from itertools import filterfalse, groupby, islice, tee
import sys
from typing import Literal, Optional, TypeVar, Union
from arelle import Cntlr, FileSource
from arelle.ModelXbrl import ModelXbrl
from arelle.ModelInstanceObject import ModelFact, ModelContext
from pathlib import Path
from zipfile import ZipFile
from concurrent.futures import ProcessPoolExecutor, as_completed
import json

from pydantic import BaseModel, Field, ValidationError

XBRL_ROOT_PATH = Path("xbrl-files")
COMPANY_FOLDERS = XBRL_ROOT_PATH.glob("*")
RESULT_ROOT_PATH = Path("json-data")
RESULT_ROOT_PATH.mkdir(parents=True, exist_ok=True)

class ProfitAndLossJP(BaseModel):
    docId: str
    accountStandard: Literal["Japan GAAP"] = Field(default="Japan GAAP")
    DurationFrom: datetime
    DurationTo: datetime
    Unit: str

    # 売上高
    NetSales: int
    # 売上総利益又は売上総損失（△）
    GrossProfit: int
    # 営業利益又は営業損失（△）
    OperatingIncome: int
    # 全事業営業利益又は全事業営業損失（△）？
    # OperatingIncomeTotalBusiness: int
    # 経常利益又は経常損失（△）
    OrdinaryIncome: int
    # 税引前当期純利益又は税引前当期純損失（△）
    IncomeBeforeIncomeTaxes: int
    # 当期純利益又は当期純損失（△）
    ProfitLoss: int
    # 包括利益
    ComprehensiveIncome: int

    # 売上原価
    CostOfSales: int
    # 販売費及び一般管理費
    SellingGeneralAndAdministrativeExpenses: int

class BalanceSheetJP(BaseModel):
    docId: str
    accountStandard: Literal["Japan GAAP"] = Field(default="Japan GAAP")
    Period: datetime
    Unit: str

    # 流動資産
    CurrentAssets: int
    # 有形固定資産
    PropertyPlantAndEquipment: int
    # 無形固定資産
    IntangibleAssets: int
    # 投資その他の資産
    InvestmentsAndOtherAssets: int
    # 固定資産
    NoncurrentAssets: int
    # 繰越資産
    # DeferredAssets: int
    # 資産
    Assets: int

    # 流動負債
    CurrentLiabilities: int
    # 固定負債
    NoncurrentLiabilities: int
    # 負債
    Liabilities: int

    # 資本金
    CapitalStock: int
    # 利益剰余金
    RetainedEarnings: int
    # 純資産
    NetAssets: int
    # 負債純資産
    LiabilitiesAndNetAssets: int

class CashFlowJP(BaseModel):
    docId: str
    accountStandard: Literal["Japan GAAP"] = Field(default="Japan GAAP")
    DurationFrom: datetime
    DurationTo: datetime
    Unit: str

    # 営業活動によるキャッシュ・フロー
    NetCashProvidedByUsedInOperatingActivities: int
    # 投資活動によるキャッシュ・フロー
    NetCashProvidedByUsedInInvestmentActivities: int
    # 財務活動によるキャッシュ・フロー
    NetCashProvidedByUsedInFinancingActivities: int

class ProfitAndLossIFRS(BaseModel):
    docId: str
    accountStandard: Literal["IFRS"] = Field(default="IFRS")
    DurationFrom: datetime
    DurationTo: datetime
    Unit: str

    # 売上高
    NetSalesIFRS: int
    # 営業利益（△損失）
    OperatingProfitLossIFRS: int
    # 税引前利益（△損失）
    ProfitLossBeforeTaxIFRS: int
    # 当期利益（△損失）
    ProfitLossIFRS: int
    # 包括利益
    ComprehensiveIncomeIFRS: int

    # 売上原価
    CostOfSalesIFRS: int
    # 販売費及び一般管理費
    SellingGeneralAndAdministrativeExpensesIFRS: int

class BalanceSheetIFRS(BaseModel):
    docId: str
    accountStandard: Literal["IFRS"] = Field(default="IFRS")
    Period: datetime
    Unit: str

    # 流動資産
    CurrentAssetsIFRS: int
    # 有形固定資産
    PropertyPlantAndEquipmentIFRS: int
    # のれん及び無形資産
    GoodwillAndIntangibleAssetsIFRS: int
    # 非流動資産
    NonCurrentAssetsIFRS: int
    # 資産
    AssetsIFRS: int

    # 流動負債
    TotalCurrentLiabilitiesIFRS: int
    # 非流動負債
    NonCurrentLabilitiesIFRS: int
    # 負債
    LiabilitiesIFRS: int

    # 資本金
    ShareCapitalIFRS: int
    # 利益剰余金
    RetainedEarningsIFRS: int
    # 資本
    EquityIFRS: int

class CashFlowIFRS(BaseModel):
    docId: str
    accountStandard: Literal["IFRS"] = Field(default="IFRS")
    DurationFrom: datetime
    DurationTo: datetime
    Unit: str

    # 営業活動によるキャッシュ・フロー
    NetCashProvidedByUsedInOperatingActivitiesIFRS: int
    # 投資活動によるキャッシュ・フロー
    NetCashProvidedByUsedInInvestingActivitiesIFRS: int
    # 財務活動によるキャッシュ・フロー
    NetCashProvidedByUsedInFinancingActivitiesIFRS: int

class Company(BaseModel):
    name: str
    edinetCode: str
    fundCode: Optional[str]
    # 事業説明
    businessDescription: str


PL_TYPE = Union[ProfitAndLossJP, ProfitAndLossIFRS]
BS_TYPE = Union[BalanceSheetJP, BalanceSheetIFRS]
CF_TYPE = Union[CashFlowJP, CashFlowIFRS]


class DocumentMetadata(BaseModel):
    seqNumber: int
    docID: str
    edinetCode: str
    # 証券コード
    secCode: Optional[str]
    # 法人番号
    JCN: str
    filerName: str
    fundCode: Optional[str]
    ordinanceCode: str
    formCode: str
    docTypeCode: str
    periodStart: Optional[str]
    periodEnd: Optional[str]
    submitDateTime: str
    docDescription: str
    issuerEdinetCode: Optional[str]
    subjectEdinetCode: Optional[str]
    subsidiaryEdinetCode: Optional[str]
    currentReportReason: Optional[str]
    parentDocID: Optional[str]
    opeDateTime: Optional[str]
    withdrawalStatus: Literal["0", "1", "2"]
    docInfoEditStatus: Literal["0", "1", "2"]
    disclosureStatus: Literal["0", "1", "2"]
    xbrlFlag: Literal["0", "1"]
    pdfFlag: Literal["0", "1"]
    attachDocFlag: Literal["0", "1"]
    englishDocFlag: Literal["0", "1"]
    csvFlag: Literal["0", "1"]
    legalStatus: Literal["0", "1", "2"]

class FinancialStatements(BaseModel):
    company: Company
    accountingStandards: Literal["Japan GAAP", "IFRS", "US GAAP"]
    docType: Literal["Annual", "Quarterly", "SemiAnnual"]
    submittionDate: datetime
    consolidatedFinancialStatements: bool
    financialYearStartDate: datetime
    financialYearEndDate: datetime
    fiscalYear: str
    formattedFiscalYear: str
    docId: str
    docMetadata: DocumentMetadata
    PL: Optional[list[PL_TYPE]]
    BS: Optional[list[BS_TYPE]]
    CF: Optional[list[CF_TYPE]]

class FinancialStatementDocument(BaseModel):
    docId: str
    docType: Literal["Annual", "Quarterly", "SemiAnnual"]
    financialYearStartDate: datetime
    financialYearEndDate: datetime
    fiscalYear: str
    submittionDate: datetime
    hasPDF: bool
    hasXBRL: bool
    hasCSV: bool

class AggregatedFinancialStatements(BaseModel):
    docs: list[FinancialStatementDocument]
    yearlyProfitAndLossStatements: list[PL_TYPE]
    semiAnnualProfitAndLossStatements: list[PL_TYPE]
    quarterlyProfitAndLossStatements: list[PL_TYPE]
    balanceSheets: list[BS_TYPE]
    yearlyCashFlowStatements: list[CF_TYPE]
    semiAnnualCashFlowStatements: list[CF_TYPE]
    quarterlyCashFlowStatements: list[CF_TYPE]


COMPANY_NAME_KEY = "FilerNameInJapaneseDEI"
ACCOUNTING_STANDARDS_KEY = "AccountingStandardsDEI"
CONSOLIDATED_FINANCIAL_STATEMENTS_KEY = "WhetherConsolidatedFinancialStatementsArePreparedDEI"
FINANCIAL_YEAR_START_DATE_KEY = "CurrentFiscalYearStartDateDEI"
FINANCIAL_YEAR_END_DATE_KEY = "CurrentFiscalYearEndDateDEI"
TERM_KEYS = [
    "FiscalYearCoverPage",
    "SemiAnnualAccountingPeriodCoverPage",
    "QuarterlyAccountingPeriodCoverPage",
    "AccountingPeriodCoverPage",
    "SemiAnnualAccountingPeriodCoverPage",
    "QuarterlyAccountingPeriodCoverPage",
]
BUSSINESS_DESCRIPTION_KEY = "DescriptionOfBusinessTextBlock"
EDINET_CODE_KEY = "EDINETCodeDEI"
FUND_CODE_KEY = "FundCodeDEI"

def extract_company_info(modelXbrl: ModelXbrl) -> Company:
    company_name_set = modelXbrl.factsByLocalName[COMPANY_NAME_KEY]  
    assert len(company_name_set) == 1
    company_name = list(company_name_set)[0].value

    bussiness_description_set = modelXbrl.factsByLocalName[BUSSINESS_DESCRIPTION_KEY]
    bussiness_description = list(bussiness_description_set)[0].value if len(bussiness_description_set) == 1 else None

    edinet_code_set = modelXbrl.factsByLocalName[EDINET_CODE_KEY]
    assert len(edinet_code_set) == 1
    edinet_code = list(edinet_code_set)[0].value

    fund_code_set = modelXbrl.factsByLocalName[FUND_CODE_KEY]
    fund_code = list(fund_code_set)[0].value if len(fund_code_set) == 1 else None

    assert bussiness_description is not None or fund_code is not None, f"if bussiness_description is None, fund_code must not be None, but bussiness_description_set: {bussiness_description_set}, fund_code_set: {fund_code_set}"

    return Company(
        name=company_name,
        edinetCode=edinet_code,
        businessDescription=bussiness_description,
        fundCode=fund_code
    )


T = TypeVar("T")
def extract_duration_type_cls(modelXbrl: ModelXbrl, DataCls: T, doc_id: str) -> list[T]:
    item_facts: list[ModelFact] = []
    for item in DataCls.__annotations__.keys():
        item_facts += list(modelXbrl.factsByLocalName[item])

    if len(item_facts) == 0:
        return []
    
    extracted_pls: list[T] = []
    item_facts = sorted(item_facts, key=lambda fact: fact.contextID)
    for context_id, facts in groupby(item_facts, key=lambda fact: fact.contextID):
        facts = list(facts)
        context: ModelContext = modelXbrl.contexts[context_id]
        if not context.isStartEndPeriod:
            print(f"Context is not StartEndPeriod: {context_id}")
            continue
        duration_from = None
        if isinstance(context.startDatetime, datetime):
            duration_from = context.startDatetime
        else:
            print(f"Invalid startDatetime: {context.startDatetime}")
            continue
        
        duration_to = None
        if isinstance(context.endDatetime, datetime):
            duration_to = context.endDatetime
        else:
            print(f"Invalid endDatetime: {context.endDatetime}")
            continue

        unit_id = facts[0].unitID
        unit_model = modelXbrl.units[unit_id]
        if unit_model is None:
            print(f"Unit not found: {unit_id}")
            continue

        unit = unit_model.value

        account_item_dict = {fact.localName: fact.value for fact in facts}

        extracted_pl = None
        try:
            extracted_pl = DataCls(
                **account_item_dict,
                DurationFrom=duration_from,
                DurationTo=duration_to,
                Unit=unit,
                docId=doc_id
            )
        except ValidationError as e:
            continue
        extracted_pls.append(extracted_pl)

    return extracted_pls

def extract_period_type_cls(modelXbrl: ModelXbrl, DataCls: T, doc_id: str) -> list[T]:
    item_facts: list[ModelFact] = []
    for item in DataCls.__annotations__.keys():
        item_facts += list(modelXbrl.factsByLocalName[item])

    if len(item_facts) == 0:
        return []
    
    extracted_pls: list[T] = []
    item_facts = sorted(item_facts, key=lambda fact: fact.contextID)
    for context_id, facts in groupby(item_facts, key=lambda fact: fact.contextID):
        facts = list(facts)
        context: ModelContext = modelXbrl.contexts[context_id]
        if not context.isInstantPeriod:
            print(f"Context is not InstantPeriod: {context_id}")
            continue
        period = None
        if isinstance(context.instantDatetime, datetime):
            period = context.instantDatetime.strftime("%Y-%m-%d")
        else:
            print(f"Invalid period: {context.instantDatetime}")
            continue

        unit_id = facts[0].unitID
        unit_model = modelXbrl.units[unit_id]
        if unit_model is None:
            print(f"Unit not found: {unit_id}")
            continue

        unit = unit_model.value

        account_item_dict = {fact.localName: fact.value for fact in facts}

        extracted_pl = None
        try:
            extracted_pl = DataCls(
                **account_item_dict,
                Period=period,
                Unit=unit,
                docId=doc_id
            )
        except ValidationError as e:
            continue

        extracted_pls.append(extracted_pl)

    return extracted_pls


def extract_pl(modelXbrl: ModelXbrl, doc_id: str) -> list[PL_TYPE]:
    return extract_duration_type_cls(modelXbrl, ProfitAndLossJP, doc_id) + extract_duration_type_cls(modelXbrl, ProfitAndLossIFRS, doc_id)

def extract_bs(modelXbrl: ModelXbrl, doc_id: str) -> list[BS_TYPE]:
    return extract_period_type_cls(modelXbrl, BalanceSheetJP, doc_id) + extract_period_type_cls(modelXbrl, BalanceSheetIFRS, doc_id)

def extract_cf(modelXbrl: ModelXbrl, doc_id: str) -> list[CF_TYPE]:
    return extract_duration_type_cls(modelXbrl, CashFlowJP, doc_id) + extract_duration_type_cls(modelXbrl, CashFlowIFRS, doc_id)

def extract_financial_statements(modelXbrl: ModelXbrl, doc_type: Literal[
    "Annual", "Quarterly", "SemiAnnual"
], document_metadata: DocumentMetadata) -> FinancialStatements:
    doc_id = document_metadata.docID
    submittion_date = datetime.strptime(document_metadata.submitDateTime, "%Y-%m-%d %H:%M")
    company = extract_company_info(modelXbrl)
    accounting_standards_set = modelXbrl.factsByLocalName[ACCOUNTING_STANDARDS_KEY]
    assert len(accounting_standards_set) == 1
    accounting_standards = list(accounting_standards_set)[0].value

    consolidated_financial_statements_set = modelXbrl.factsByLocalName[CONSOLIDATED_FINANCIAL_STATEMENTS_KEY]
    assert len(consolidated_financial_statements_set) == 1
    consolidated_financial_statements = list(consolidated_financial_statements_set)[0].value

    financial_year_start_date_set = modelXbrl.factsByLocalName[FINANCIAL_YEAR_START_DATE_KEY]
    assert len(financial_year_start_date_set) == 1
    financial_year_start_date = list(financial_year_start_date_set)[0].value

    financial_year_end_date_set = modelXbrl.factsByLocalName[FINANCIAL_YEAR_END_DATE_KEY]
    assert len(financial_year_end_date_set) == 1
    financial_year_end_date = list(financial_year_end_date_set)[0].value

    fiscal_year_set: set[ModelFact] = set()
    for term_key in TERM_KEYS:
        fiscal_year_set |= modelXbrl.factsByLocalName[term_key]
    assert len(fiscal_year_set) == 1, f"{len(fiscal_year_set)} fiscal year found in {company.name}, financial_year_start_date: {financial_year_start_date}, financial_year_end_date: {financial_year_end_date}"
    fiscal_year = list(fiscal_year_set)[0].value

    pl = extract_pl(modelXbrl, doc_id)
    bs = extract_bs(modelXbrl, doc_id)
    cf = extract_cf(modelXbrl, doc_id)

    return FinancialStatements(
        docId=doc_id,
        company=company,
        docMetadata=document_metadata,
        docType=doc_type,
        submittionDate=submittion_date,
        accountingStandards=accounting_standards,
        consolidatedFinancialStatements=consolidated_financial_statements,
        financialYearStartDate=financial_year_start_date,
        financialYearEndDate=financial_year_end_date,
        fiscalYear=fiscal_year,
        formattedFiscalYear=format_fiscal_year(fiscal_year),
        PL=pl,
        BS=bs,
        CF=cf
    )

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


# extract 第76期 from 第76期（自　2022年６月１日　至　2023年５月31日） 
# extract 第75期第３四半期 from 第75期第３四半期（自　2021年12月１日　至　2022年２月28日）
def format_fiscal_year(fiscal_year: str) -> str:
    extracted = fiscal_year.split("（")[0]
    return extracted

def aggreagete_financial_statements(financial_statements_list: list[FinancialStatements]) -> AggregatedFinancialStatements:
    docs: list[FinancialStatementDocument] = []
    doc_id_to_doc: dict[str, FinancialStatementDocument] = {}
    for financial_statements in financial_statements_list:
        doc = (FinancialStatementDocument(
            docId=financial_statements.docId,
            docType=financial_statements.docType,
            financialYearStartDate=financial_statements.financialYearStartDate,
            financialYearEndDate=financial_statements.financialYearEndDate,
            fiscalYear=format_fiscal_year(financial_statements.fiscalYear),
            submittionDate=financial_statements.submittionDate,
            hasPDF=financial_statements.docMetadata.pdfFlag == "1",
            hasXBRL=financial_statements.docMetadata.xbrlFlag == "1",
            hasCSV=financial_statements.docMetadata.csvFlag == "1"
        ))
        docs.append(doc)
        doc_id_to_doc[financial_statements.docId] = doc
    
    docs = reversed(sorted(docs, key=lambda doc: doc.submittionDate))

    annual_pls: list[PL_TYPE] = []
    semianual_pls: list[PL_TYPE] = []
    quarterly_pls: list[PL_TYPE] = []
    bss: list[BS_TYPE] = []
    annual_fcs: list[CF_TYPE] = []
    semianual_fcs: list[CF_TYPE] = []
    quarterly_fcs: list[CF_TYPE] = []
    for financial_statements in financial_statements_list:
        # PL
        for pl in financial_statements.PL:
            month_duration = calc_month_duration(
                pl.DurationFrom.month,
                pl.DurationTo.month
            )
            if month_duration == 0:
                annual_pls.append(pl)
            elif month_duration == 6:
                semianual_pls.append(pl)
            elif month_duration == 3 or month_duration == 9:
                quarterly_pls.append(pl)

        # BS
        for bs in financial_statements.BS:
            bss.append(bs)
        
        # CF
        for cf in financial_statements.CF:
            month_duration = calc_month_duration(
                cf.DurationFrom.month,
                cf.DurationTo.month
            )
            if month_duration == 0:
                annual_fcs.append(cf)
            elif month_duration == 6:
                semianual_fcs.append(cf)
            elif month_duration == 3 or month_duration == 9:
                quarterly_fcs.append(cf)

    annual_pls = sorted(annual_pls, key=lambda pl: pl.DurationFrom)
    semianual_pls = sorted(semianual_pls, key=lambda pl: pl.DurationFrom)
    quarterly_pls = sorted(quarterly_pls, key=lambda pl: pl.DurationFrom)
    def pl_key(pl: PL_TYPE) -> str:
        return f"{pl.DurationFrom}_{pl.DurationTo}"
    def deduplicate_pl_with_selecting_original_doc(pls: list[PL_TYPE]) -> list[PL_TYPE]:
        deduplicated_pls_dict: dict[str, PL_TYPE] = {}
        for pl in pls:
            if pl_key(pl) not in deduplicated_pls_dict:
                deduplicated_pls_dict[pl.docId] = pl
            else:
                new_pl_doc = doc_id_to_doc[pl.docId]
                old_pl_doc = doc_id_to_doc[deduplicated_pls_dict[pl.docId].docId]
                # 初出のほうを選択
                if new_pl_doc.financialYearStartDate < old_pl_doc.financialYearStartDate:
                    deduplicated_pls_dict[pl.docId] = pl

        deduplicated_pls = list(deduplicated_pls_dict.values())
        deduplicated_pls = sorted(deduplicated_pls, key=lambda pl: pl.DurationFrom)        
        return deduplicated_pls
    annual_pls = deduplicate_pl_with_selecting_original_doc(annual_pls)
    semianual_pls = deduplicate_pl_with_selecting_original_doc(semianual_pls)
    quarterly_pls = deduplicate_pl_with_selecting_original_doc(quarterly_pls)

    bss = sorted(bss, key=lambda bs: bs.Period)
    def bs_key(bs: BS_TYPE) -> str:
        return bs.Period
    def deduplicate_bs_with_selecting_original_doc(bss: list[BS_TYPE]) -> list[BS_TYPE]:
        deduplicated_bss_dict: dict[str, BS_TYPE] = {}
        for bs in bss:
            if bs_key(bs) not in deduplicated_bss_dict:
                deduplicated_bss_dict[bs.docId] = bs
            else:
                new_bs_doc = doc_id_to_doc[bs.docId]
                old_bs_doc = doc_id_to_doc[deduplicated_bss_dict[bs.docId].docId]
                # 初出のほうを選択
                if new_bs_doc.financialYearStartDate < old_bs_doc.financialYearStartDate:
                    deduplicated_bss_dict[bs.docId] = bs

        deduplicated_bss = list(deduplicated_bss_dict.values())
        deduplicated_bss = sorted(deduplicated_bss, key=lambda bs: bs.Period)
        return deduplicated_bss
    bss = deduplicate_bs_with_selecting_original_doc(bss)

    annual_fcs = sorted(annual_fcs, key=lambda cf: cf.DurationFrom)
    semianual_fcs = sorted(semianual_fcs, key=lambda cf: cf.DurationFrom)
    quarterly_fcs = sorted(quarterly_fcs, key=lambda cf: cf.DurationFrom)
    def cf_key(cf: CF_TYPE) -> str:
        return f"{cf.DurationFrom}_{cf.DurationTo}"
    def deduplicate_cf_with_selecting_original_doc(fcs: list[CF_TYPE]) -> list[CF_TYPE]:
        deduplicated_fcs_dict: dict[str, CF_TYPE] = {}
        for cf in fcs:
            if cf_key(cf) not in deduplicated_fcs_dict:
                deduplicated_fcs_dict[cf.docId] = cf
            else:
                new_cf_doc = doc_id_to_doc[cf.docId]
                old_cf_doc = doc_id_to_doc[deduplicated_fcs_dict[cf.docId].docId]
                # 初出のほうを選択
                if new_cf_doc.financialYearStartDate < old_cf_doc.financialYearStartDate:
                    deduplicated_fcs_dict[cf.docId] = cf

        deduplicated_fcs = list(deduplicated_fcs_dict.values())
        deduplicated_fcs = sorted(deduplicated_fcs, key=lambda cf: cf.DurationFrom)
        return deduplicated_fcs
    annual_fcs = deduplicate_cf_with_selecting_original_doc(annual_fcs)
    semianual_fcs = deduplicate_cf_with_selecting_original_doc(semianual_fcs)
    quarterly_fcs = deduplicate_cf_with_selecting_original_doc(quarterly_fcs)

    return AggregatedFinancialStatements(
        yearlyProfitAndLossStatements=annual_pls,
        semiAnnualProfitAndLossStatements=semianual_pls,
        quarterlyProfitAndLossStatements=quarterly_pls,
        balanceSheets=bss,
        yearlyCashFlowStatements=annual_fcs,
        semiAnnualCashFlowStatements=semianual_fcs,
        quarterlyCashFlowStatements=quarterly_fcs,
        docs=docs
    )

def construct_result_file_path(edinet_code: str) -> Path:
    return RESULT_ROOT_PATH / f"{edinet_code}" / "result.json"
def is_result_file_exists(edinet_code: str) -> bool:
    return construct_result_file_path(edinet_code).exists()

def process_company_financial_statements_extraction(company_folder: Path, result_file_path: Path, log_prefix: str = ""):
    print(f"{log_prefix}Processing {company_folder}")
    edinet_code = company_folder.name
    company_financial_statements: list[FinancialStatements] = []

    archive_files = company_folder.glob("*/*_xbrl.zip")
    for archive_file in archive_files:
        print(f"{log_prefix}Processing {archive_file}")
        _submittion_date, _doc_id, doc_type = archive_file.parent.name.split("_")
        doc_type_map = {
            "有価証券報告書": "Annual",
            "四半期報告書": "Quarterly",
            "半期報告書": "SemiAnnual",
        }
        # --------------------
        # find entry point
        # --------------------
        archived_files = ZipFile(archive_file).namelist()
        entry_points_canditates = []
        for archived_file_path in archived_files:
            archived_file_path = Path(archived_file_path)
            if archived_file_path.match("XBRL/PublicDoc/*.xbrl"):
                entry_points_canditates.append(archived_file_path)

        if len(entry_points_canditates) == 0:
            print(f"Entry point not found in {archive_file}")
            continue
        elif len(entry_points_canditates) > 1:
            print(f"Multiple entry points found in {archive_file}")
            continue
        assert len(entry_points_canditates) == 1
        entry_point = entry_points_canditates[0]

        # --------------------
        # load xbrl file
        # --------------------
        target_file_with_entry_point =  archive_file / entry_point
        document_metadata_file = archive_file.parent / "metadata.json"
        loaded_document_metadata = json.loads(document_metadata_file.read_text())
        document_metadata = DocumentMetadata(
            **loaded_document_metadata
        )
    
        cntlr = Cntlr.Cntlr(logFileName="logToPrint")
        cntlr.startLogging()
        target_file = FileSource.openFileSource(str(target_file_with_entry_point))
        cntlr.modelManager.load(target_file)

        loaded_model_xbrls: list[ModelXbrl] = cntlr.modelManager.loadedModelXbrls
        assert len(loaded_model_xbrls) == 1, f"Loading {target_file_with_entry_point} failed, multiple modelXbrls loaded"
        for modelXbrl in loaded_model_xbrls:
            print(f"{log_prefix} {modelXbrl.fileSource.url}")

            financial_statements = extract_financial_statements(modelXbrl, doc_type=doc_type_map[doc_type], document_metadata=document_metadata)
            company_financial_statements.append(financial_statements)

        cntlr.close()

    
    company_financial_statements = sorted(company_financial_statements, key=lambda financial_statements: financial_statements.submittionDate)
    company_financial_statements = list(reversed(company_financial_statements))
    company_financial_statements_dicts = [financial_statements.model_dump(
        mode="json"
    ) for financial_statements in company_financial_statements]
    aggregated_financial_statements = aggreagete_financial_statements(company_financial_statements)

    if len(company_financial_statements) == 0:
        print(f"{log_prefix}No xbrl files found in {company_folder}")
        return

    latest_document_metadata = company_financial_statements[0].docMetadata
    secCode = latest_document_metadata.secCode
    jcn = latest_document_metadata.JCN

    result_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(result_file_path, "w") as f:        
        json.dump({
            "company": {
                "edinetCode": edinet_code,
                "name": latest_document_metadata.filerName,
                "secCode": secCode,
                "jcn": jcn
            },
            "docs": [doc.model_dump(mode="json") for doc in aggregated_financial_statements.docs],
            "aggregatedFinancialStatements": aggregated_financial_statements.model_dump(mode="json"),
            "financialStatements": company_financial_statements_dicts
        }, f, indent=2, ensure_ascii=False)

    print(f"{log_prefix}Saved to {result_file_path}")

COMPANY_FOLDERS = filterfalse(lambda company_folder: is_result_file_exists(
    company_folder.name
), COMPANY_FOLDERS)
COMPANY_FOLDERS = islice(COMPANY_FOLDERS, 10)
COMPANY_FOLDERS, _COMPANY_FOLDERS = tee(COMPANY_FOLDERS)
TOTAL_LENGTH = len(list(_COMPANY_FOLDERS))

if __name__ == "__main__":
    try:
        with ProcessPoolExecutor(
            max_workers=10
        ) as executor:
            futures = []
            for index, company_folder in enumerate(COMPANY_FOLDERS):
                result_file_path = construct_result_file_path(
                    company_folder.name,
                )
                future = executor.submit(process_company_financial_statements_extraction, company_folder, result_file_path, f"[{index + 1}/{TOTAL_LENGTH}] ")
                futures.append(future)

            for future in as_completed(futures):
                future.result()
    except KeyboardInterrupt:
        print("\nInterrupt received! Stopping processes...")
        executor.shutdown(wait=True, cancel_futures=True)
        sys.exit(0)

    print("Done")
