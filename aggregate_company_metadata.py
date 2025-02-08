from itertools import islice
import json
from pathlib import Path
from pprint import pprint
from typing import Optional

from pydantic import BaseModel

from extract_financial_statements_from_xbrl import (
    Company,
    FinancialStatements,
    CF_TYPE,
    BS_TYPE,
    PL_TYPE,
)

class AggregatedFinancialStatements(BaseModel):
    yearlyProfitAndLossStatements: list[PL_TYPE]
    semiAnnualProfitAndLossStatements: list[PL_TYPE]
    quarterlyProfitAndLossStatements: list[PL_TYPE]
    balanceSheets: list[BS_TYPE]
    yearlyCashFlowStatements: list[CF_TYPE]
    semiAnnualCashFlowStatements: list[CF_TYPE]
    quarterlyCashFlowStatements: list[CF_TYPE]

class SavedFinancialStatements(BaseModel):
    company: Company
    aggregatedFinancialStatements: AggregatedFinancialStatements
    financialStatements: list[FinancialStatements]

class SummarizedCompany(BaseModel):
    fileName: str
    companyName: str
    edinetCode: str
    fundCode: Optional[str]
    yearlyPLNum: int
    semiAnnualPLNum: int
    quarterlyPLNum: int
    bsNum: int
    yearlyCFNum: int
    semiAnnualCFNum: int
    quarterlyCFNum: int
    latestPL: Optional[PL_TYPE]
    latestBS: Optional[BS_TYPE]
    latestCF: Optional[CF_TYPE]


def load_financial_statements_from_json(file_path: Path) -> FinancialStatements:
    with open(file_path, "r") as f:
        data = json.load(f)

    company = Company(**data["company"], fundCode=None, businessDescription="")
    financial_statements = [
        FinancialStatements(**fs) for fs in data["financialStatements"]
    ]
    aggregated_financial_statements = AggregatedFinancialStatements(**data["aggregatedFinancialStatements"])

    return SavedFinancialStatements(
        company=company,
        financialStatements=financial_statements,
        aggregatedFinancialStatements=aggregated_financial_statements,
    )

JSON_DATA_DIR = Path("json-data")    
AGGREAGED_DATA_FILE = JSON_DATA_DIR / "summarized_companies.json"
json_files = JSON_DATA_DIR.glob("*/*.json")

financial_statements_list: list[tuple[str, SavedFinancialStatements]] = []
# json_files = list(islice(json_files, 10))
for json_file in json_files:
    loaded_financial_statements = load_financial_statements_from_json(json_file)
    financial_statements_list.append((json_file.parent.name, loaded_financial_statements))

print(f"loaded {len(financial_statements_list)} financial statements")

summarized_companies: list[SummarizedCompany] = []
for file_path, financial_statement in financial_statements_list:

    latest_annual_statements = None
    for fs in financial_statement.financialStatements:
        if fs.docType == "Annual":
            if latest_annual_statements is None or latest_annual_statements.financialYearStartDate < fs.financialYearStartDate:
                latest_annual_statements = fs

    latest_pl = None
    latest_bs = None
    latest_cf = None

    if latest_annual_statements is not None:
        if latest_annual_statements.PL is not None and len(latest_annual_statements.PL) > 0:
            latest_pl = sorted(latest_annual_statements.PL, key=lambda pl: pl.DurationFrom).pop()
        if latest_annual_statements.BS is not None and len(latest_annual_statements.BS) > 0:
            latest_bs = sorted(latest_annual_statements.BS, key=lambda bs: bs.Period).pop()
        if latest_annual_statements.CF is not None and len(latest_annual_statements.CF) > 0:
            latest_cf = sorted(latest_annual_statements.CF, key=lambda cf: cf.DurationFrom).pop()

    summarized_companies.append(
        SummarizedCompany(
            fileName=file_path,
            companyName=financial_statement.company.name,
            edinetCode=financial_statement.company.edinetCode,
            fundCode=financial_statement.company.fundCode,
            yearlyPLNum=len(financial_statement.aggregatedFinancialStatements.yearlyProfitAndLossStatements),
            semiAnnualPLNum=len(financial_statement.aggregatedFinancialStatements.semiAnnualProfitAndLossStatements),
            quarterlyPLNum=len(financial_statement.aggregatedFinancialStatements.quarterlyProfitAndLossStatements),
            bsNum=len(financial_statement.aggregatedFinancialStatements.balanceSheets),
            yearlyCFNum=len(financial_statement.aggregatedFinancialStatements.yearlyCashFlowStatements),
            semiAnnualCFNum=len(financial_statement.aggregatedFinancialStatements.semiAnnualCashFlowStatements),
            quarterlyCFNum=len(financial_statement.aggregatedFinancialStatements.quarterlyCashFlowStatements),
            latestPL=latest_pl,
            latestBS=latest_bs,
            latestCF=latest_cf,
        )   
    )

with open(AGGREAGED_DATA_FILE, "w") as f:
    json.dump([sc.model_dump(mode="json") for sc in summarized_companies], f, ensure_ascii=False, indent=2)