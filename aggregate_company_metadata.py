from itertools import islice
import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, model_serializer


from extract_financial_statements_from_xbrl_v2 import (
    AggregatedFinancialStatement,
    Company,
    FinancialStatementDocument,
)
from xbrl_utils import AccountingItem, PLInstance, BSInstance, CFInstance


class SimpleAccountingItem(AccountingItem):
    @model_serializer(when_used="json")
    def ser_model(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            # 明示的に記述しないと、recursion error が発生する
            "items": [item.model_dump(mode="json") for item in self.items],
        }


class SimplePLInstance(PLInstance):
    operatingIncome: SimpleAccountingItem
    netSales: list[SimpleAccountingItem]
    expenses: list[SimpleAccountingItem]
    profitAndLoss: SimpleAccountingItem

    @model_serializer(when_used="json")
    def ser_model(self) -> dict:
        return {
            "accountStandard": self.accountStandard,
            "durationFrom": self.durationFrom,
            "durationTo": self.durationTo,
            "consolidated": self.consolidated,
            "operatingIncome": self.operatingIncome.model_dump(mode="json"),
            "netSales": [item.model_dump(mode="json") for item in self.netSales],
            "expenses": [item.model_dump(mode="json") for item in self.expenses],
            "unit": self.unit,
            "docId": self.docId,
        }


class SimpleBSInstance(BSInstance):
    assets: SimpleAccountingItem
    liabilities: SimpleAccountingItem
    net_assets: SimpleAccountingItem

    @model_serializer(when_used="json")
    def ser_model(self) -> dict:
        return {
            "accountStandard": self.accountStandard,
            "period": self.period,
            "consolidated": self.consolidated,
            "assets": self.assets.model_dump(mode="json"),
            "liabilities": self.liabilities.model_dump(mode="json"),
            "net_assets": self.net_assets.model_dump(mode="json"),
            "unit": self.unit,
            "docId": self.docId,
        }


class SimpleCFInstance(CFInstance):
    operating: SimpleAccountingItem
    investing: SimpleAccountingItem
    financing: SimpleAccountingItem

    @model_serializer(when_used="json")
    def ser_model(self) -> dict:
        return {
            "accountStandard": self.accountStandard,
            "durationFrom": self.durationFrom,
            "durationTo": self.durationTo,
            "consolidated": self.consolidated,
            "operating": self.operating.model_dump(mode="json"),
            "investing": self.investing.model_dump(mode="json"),
            "financing": self.financing.model_dump(mode="json"),
            "unit": self.unit,
            "docId": self.docId,
        }


class SimpleFinancialStatementDocument(FinancialStatementDocument):
    pl: list[SimplePLInstance]
    bs: list[SimpleBSInstance]
    cf: list[SimpleCFInstance]


class SimpleAggregatedFinancialStatements(AggregatedFinancialStatement):
    consolidatedYearlyProfitAndLossStatements: list[SimplePLInstance]
    consolidatedSemiAnnualProfitAndLossStatements: list[SimplePLInstance]
    consolidatedQuarterlyProfitAndLossStatements: list[SimplePLInstance]
    consolidatedBalanceSheets: list[SimpleBSInstance]
    consolidatedYearlyCashFlowStatements: list[SimpleCFInstance]
    consolidatedSemiAnnualCashFlowStatements: list[SimpleCFInstance]
    consolidatedQuarterlyCashFlowStatements: list[SimpleCFInstance]
    nonConsolidatedYearlyProfitAndLossStatements: list[SimplePLInstance]
    nonConsolidatedSemiAnnualProfitAndLossStatements: list[SimplePLInstance]
    nonConsolidatedQuarterlyProfitAndLossStatements: list[SimplePLInstance]
    nonConsolidatedBalanceSheets: list[SimpleBSInstance]
    nonConsolidatedYearlyCashFlowStatements: list[SimpleCFInstance]
    nonConsolidatedSemiAnnualCashFlowStatements: list[SimpleCFInstance]
    nonConsolidatedQuarterlyCashFlowStatements: list[SimpleCFInstance]


class SimpleCompany(Company):
    aggregatedFinancialStatements: SimpleAggregatedFinancialStatements
    financialStatementDocuments: list[SimpleFinancialStatementDocument]


class SummarizedCompany(BaseModel):
    fileName: str
    companyName: str
    edinetCode: str
    yearlyPLNum: int
    semiAnnualPLNum: int
    quarterlyPLNum: int
    bsNum: int
    yearlyCFNum: int
    semiAnnualCFNum: int
    quarterlyCFNum: int
    latestPL: Optional[SimplePLInstance]
    latestBS: Optional[SimpleBSInstance]
    latestCF: Optional[SimpleCFInstance]


def load_financial_statements_from_json(file_path: Path) -> SimpleCompany:
    json_string = file_path.read_text()

    return SimpleCompany.model_validate_json(json_string)


JSON_DATA_DIR = Path("json-data-v2")
AGGREAGED_DATA_FILE = JSON_DATA_DIR / "summarized_companies.json"
json_files = JSON_DATA_DIR.glob("*/*.json")
# json_files = list(islice(json_files, 1))

# specials = [
#     JSON_DATA_DIR / "E00738" / "result.json",
# ]
# json_files = json_files + specials


financial_statements_list: list[tuple[str, SimpleCompany]] = []
for json_file in json_files:
    loaded_financial_statements = load_financial_statements_from_json(json_file)
    financial_statements_list.append(
        (json_file.parent.name, loaded_financial_statements)
    )

print(f"loaded {len(financial_statements_list)} financial statements")

summarized_companies: list[SummarizedCompany] = []
for file_path, company in financial_statements_list:
    latest_annual_statements: Optional[SimpleFinancialStatementDocument] = None
    for fs in company.financialStatementDocuments:
        if fs.docType == "Annual":
            if (
                latest_annual_statements is None
                or latest_annual_statements.submittionDate < fs.submittionDate
            ):
                latest_annual_statements = fs

    latest_pl: Optional[SimplePLInstance] = None
    latest_bs: Optional[SimpleBSInstance] = None
    latest_cf: Optional[SimpleCFInstance] = None

    placeholder_accounting_item = SimpleAccountingItem(
        nameJa="N/A",
        nameEn="N/A",
        nameDetailJa="Pleaseholder",
        nameDetailEn="Pleaseholder",
        name="N/A",
        nameDetail="Placeholder",
        value=0.0,
        items=[],
        qname="N/A",
        balance=None,
        weight_in_parent=None,
        order_in_parent=None,
    )

    if latest_annual_statements is not None:
        if len(latest_annual_statements.pl) > 0:
            latest_pl = latest_annual_statements.pl[0]
            for latest_pl_candidate in latest_annual_statements.pl:
                if latest_pl_candidate.durationFrom > latest_pl.durationFrom:
                    latest_pl = latest_pl_candidate
                elif latest_pl_candidate.durationFrom == latest_pl.durationFrom:
                    if latest_pl_candidate.durationTo > latest_pl.durationTo:
                        latest_pl = latest_pl_candidate
                    elif latest_pl_candidate.durationTo == latest_pl.durationTo:
                        if (
                            not latest_pl.consolidated
                            and latest_pl_candidate.consolidated
                        ):
                            latest_pl = latest_pl_candidate
            for expenses in latest_pl.expenses:
                for first_expense_item in expenses.items:
                    first_expense_item.items = []
            for revenues in latest_pl.netSales:
                for first_revenue_item in revenues.items:
                    first_revenue_item.items = []
        if len(latest_annual_statements.bs) > 0:
            latest_bs = latest_annual_statements.bs[0]
            for latest_bs_candidate in latest_annual_statements.bs:
                if latest_bs_candidate.period > latest_bs.period:
                    latest_bs = latest_bs_candidate
                elif latest_bs_candidate.period == latest_bs.period:
                    if not latest_bs.consolidated and latest_bs_candidate.consolidated:
                        latest_bs = latest_bs_candidate
            for assets in latest_bs.assets.items:
                assets.items = []
            for liabilities in latest_bs.liabilities.items:
                liabilities.items = []
            for equity in latest_bs.net_assets.items:
                equity.items = []
        if len(latest_annual_statements.cf) > 0:
            latest_cf = latest_annual_statements.cf[0]
            for latest_cf_candidate in latest_annual_statements.cf:
                if latest_cf_candidate.durationFrom > latest_cf.durationFrom:
                    latest_cf = latest_cf_candidate
                elif latest_cf_candidate.durationFrom == latest_cf.durationFrom:
                    if latest_cf_candidate.durationTo > latest_cf.durationTo:
                        latest_cf = latest_cf_candidate
                    elif latest_cf_candidate.durationTo == latest_cf.durationTo:
                        if (
                            not latest_cf.consolidated
                            and latest_cf_candidate.consolidated
                        ):
                            latest_cf = latest_cf_candidate
            for operating_activities in latest_cf.operating.items:
                operating_activities.items = []
            for investing_activities in latest_cf.investing.items:
                investing_activities.items = []
            for financing_activities in latest_cf.financing.items:
                financing_activities.items = []

    summarized_companies.append(
        SummarizedCompany(
            fileName=file_path,
            companyName=company.name,
            edinetCode=company.edinetCode,
            yearlyPLNum=len(
                company.aggregatedFinancialStatements.consolidatedYearlyProfitAndLossStatements
            )
            + len(
                company.aggregatedFinancialStatements.nonConsolidatedYearlyProfitAndLossStatements
            ),
            semiAnnualPLNum=len(
                company.aggregatedFinancialStatements.consolidatedSemiAnnualProfitAndLossStatements
            )
            + len(
                company.aggregatedFinancialStatements.nonConsolidatedSemiAnnualProfitAndLossStatements
            ),
            quarterlyPLNum=len(
                company.aggregatedFinancialStatements.consolidatedQuarterlyProfitAndLossStatements
            )
            + len(
                company.aggregatedFinancialStatements.nonConsolidatedQuarterlyProfitAndLossStatements
            ),
            bsNum=len(company.aggregatedFinancialStatements.consolidatedBalanceSheets)
            + len(company.aggregatedFinancialStatements.nonConsolidatedBalanceSheets),
            yearlyCFNum=len(
                company.aggregatedFinancialStatements.consolidatedYearlyCashFlowStatements
            )
            + len(
                company.aggregatedFinancialStatements.nonConsolidatedYearlyCashFlowStatements
            ),
            semiAnnualCFNum=len(
                company.aggregatedFinancialStatements.consolidatedSemiAnnualCashFlowStatements
            )
            + len(
                company.aggregatedFinancialStatements.nonConsolidatedSemiAnnualCashFlowStatements
            ),
            quarterlyCFNum=len(
                company.aggregatedFinancialStatements.consolidatedQuarterlyCashFlowStatements
            )
            + len(
                company.aggregatedFinancialStatements.nonConsolidatedQuarterlyCashFlowStatements
            ),
            latestPL=latest_pl,
            latestBS=latest_bs,
            latestCF=latest_cf,
        )
    )

with open(AGGREAGED_DATA_FILE, "w") as f:
    json.dump(
        [sc.model_dump(mode="json") for sc in summarized_companies],
        f,
        ensure_ascii=False,
        indent=2,
    )
