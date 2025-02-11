from abc import abstractmethod
from datetime import datetime
from itertools import combinations, product
from pathlib import Path
from typing import Literal, Self, TypeVar
from zipfile import ZipFile
from arelle import Cntlr, FileSource
from arelle.ModelXbrl import ModelXbrl, ModelFact, ModelContext
from arelle.ModelDtsObject import ModelConcept, ModelRelationship
from arelle import XbrlConst
from arelle.ModelRelationshipSet import ModelRelationshipSet
from pydantic import BaseModel


def load_edinet_xbrl_model_from_zip(
    zip_file_path: Path,
) -> tuple[ModelXbrl, Cntlr.Cntlr]:
    xbrls, cntlr = load_edinet_xbrl_models_from_zip(zip_file_path)
    if len(xbrls) != 1:
        raise ValueError(
            f"Expected 1 XBRL file, but got {len(xbrls)} XBRL files, loaded from {zip_file_path}"
        )
    return xbrls[0], cntlr


def load_edinet_xbrl_models_from_zip(
    zip_file_path: Path,
) -> tuple[list[ModelXbrl], Cntlr.Cntlr]:
    archived_files = ZipFile(zip_file_path).namelist()
    entry_points_canditates = []
    for archived_file_path in archived_files:
        archived_file_path = Path(archived_file_path)
        if archived_file_path.match("XBRL/PublicDoc/*.xbrl"):
            entry_points_canditates.append(archived_file_path)

    # 多分一つしかないはず
    if len(entry_points_canditates) == 0:
        raise ValueError("No XBRL files found in the archive.")
    elif len(entry_points_canditates) > 1:
        raise ValueError("Multiple XBRL files found in the archive.")

    entry_point = entry_points_canditates[0]
    target_file_with_entry_point = zip_file_path / entry_point

    xbrls, cntlr = load_ebrls_with_arelle(target_file_with_entry_point)
    return xbrls, cntlr


def load_ebrls_with_arelle(xbrl_file_path: Path) -> tuple[list[ModelXbrl], Cntlr.Cntlr]:
    cntlr = Cntlr.Cntlr(logFileName="logToPrint")
    cntlr.startLogging()
    target_file = FileSource.openFileSource(str(xbrl_file_path))
    cntlr.modelManager.load(target_file)

    loaded_model_xbrls: list[ModelXbrl] = cntlr.modelManager.loadedModelXbrls
    return loaded_model_xbrls, cntlr


# 以下の「02 . 財務諸表本表」、「03 . 国際会計基準」から
# 「2025年版EDINETタクソノミ（2025年3月31日以後に終了する事業年度に係る有価証券報告書等から適用）」をダウンロードして、
# 財務諸表のロールURLを手動でリスト化した。
# [EDINETタクソノミ及びコードリストダウンロード](https://disclosure2.edinet-fsa.go.jp/weee0010.aspx)
BS_ROLE_TYPE_JP = [
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_BalanceSheet",  # 310040 貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_BalanceSheet",  # 310040 貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_SemiAnnualBalanceSheet",  # 310050 第二種中間貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_SemiAnnualBalanceSheet",  # 310050 第二種中間貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_Type1SemiAnnualBalanceSheet",  # 310051 第一種中間貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_Type1SemiAnnualBalanceSheet",  # 310051 第一種中間貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_QuarterlyBalanceSheet",  # 310060 四半期貸借対照表（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_QuarterlyBalanceSheet",  # 310060 四半期貸借対照表（2025年版で廃止）
]
CONSOLIDATED_BS_ROLE_TYPE_JP = [
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_ConsolidatedBalanceSheet",  # 310010 連結貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_ConsolidatedBalanceSheet",  # 310010 連結貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_SemiAnnualConsolidatedBalanceSheet",  # 310020 第二種中間連結貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_SemiAnnualConsolidatedBalanceSheet",  # 310020 第二種中間連結貸借対照表
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_Type1SemiAnnualConsolidatedBalanceSheet",  # 310021 第一種中間連結貸借対照
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_QuarterlyConsolidatedBalanceSheet",  # 310030 四半期連結貸借対照表（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_QuarterlyConsolidatedBalanceSheet",  # 310030 四半期連結貸借対照表（2025年版で廃止）
]
PL_ROLE_TYPE_JP = [
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_StatementOfIncome",  # 321040 損益計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_StatementOfIncome",  # 321040 損益計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_SemiAnnualStatementOfIncome",  # 321050 第二種中間損益計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_SemiAnnualStatementOfIncome",  # 321050 第二種中間損益計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_Type1SemiAnnualStatementOfIncome",  # 321051 第一種中間損益計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_Type1SemiAnnualStatementOfIncome",  # 321051 第一種中間損益計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_YearToQuarterEndStatementOfIncome",  # 321061 四半期損益計算書　四半期累計期間（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_YearToQuarterEndStatementOfIncome",  # 321061 四半期損益計算書　四半期累計期間（2025年版で廃止）
]
CONSOLIDATED_PL_ROLE_TYPE_JP = [
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_ConsolidatedStatementOfIncome",  # 321010 連結損益（及び包括利益）計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_ConsolidatedStatementOfIncome",  # 321010 連結損益（及び包括利益）計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_SemiAnnualConsolidatedStatementOfIncome",  # 321020 第二種中間連結損益（及び包括利益）計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_SemiAnnualConsolidatedStatementOfIncome",  # 321020 第二種中間連結損益（及び包括利益）計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_Type1SemiAnnualConsolidatedStatementOfIncome",  # 321021 第一種中間連結損益（及び包括利益）計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_Type1SemiAnnualConsolidatedStatementOfIncome",  # 321021 第一種中間連結損益（及び包括利益）計算書
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_YearToQuarterEndConsolidatedStatementOfIncome",  # 321031 四半期連結損益（及び包括利益）計算書　四半期連結累計期間（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_YearToQuarterEndConsolidatedStatementOfIncome",  # 321032 四半期連結損益（及び包括利益）計算書　四半期連結会計期間（2025年版で廃止）\
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_QuarterPeriodConsolidatedStatementOfIncome",  # 321032 四半期連結損益（及び包括利益）計算書　四半期連結会計期間（2025年版で廃止）
]
CF_ROLE_TYPE_JP = [
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_StatementOfCashFlows-direct",  # 341040 キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_StatementOfCashFlows-direct",  # 341040 キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_SemiAnnualStatementOfCashFlows-direct",  # 341050 第二種中間キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_SemiAnnualStatementOfCashFlows-direct",  # 341050 第二種中間キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_Type1SemiAnnualStatementOfCashFlows-direct",  # 341051 第一種中間キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_Type1SemiAnnualStatementOfCashFlows-direct",  # 341051 第一種中間キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_QuarterlyStatementOfCashFlows-direct",  # 341060 四半期キャッシュ・フロー計算書　直接法（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_QuarterlyStatementOfCashFlows-direct",  # 341060 四半期キャッシュ・フロー計算書　直接法（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_StatementOfCashFlows-indirect",  # 342040 キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_StatementOfCashFlows-indirect",  # 342040 キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_SemiAnnualStatementOfCashFlows-indirect",  # 342050 第二種中間キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_SemiAnnualStatementOfCashFlows-indirect",  # 342050 第二種中間キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_Type1SemiAnnualStatementOfCashFlows-indirect",  # 342051 第一種中間キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_Type1SemiAnnualStatementOfCashFlows-indirect",  # 342051 第一種中間キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_QuarterlyStatementOfCashFlows-indirect",  # 342060 四半期キャッシュ・フロー計算書　間接法（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_QuarterlyStatementOfCashFlows-indirect",  # 342060 四半期キャッシュ・フロー計算書　間接法（2025年版で廃止）
]
CONSOLIDATED_CF_ROLE_TYPE_JP = [
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_ConsolidatedStatementOfCashFlows-direct",  # 341010 連結キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_ConsolidatedStatementOfCashFlows-direct",  # 341010 連結キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_SemiAnnualConsolidatedStatementOfCashFlows-direct",  # 341020 第二種中間連結キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_SemiAnnualConsolidatedStatementOfCashFlows-direct",  # 341020 第二種中間連結キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_Type1SemiAnnualConsolidatedStatementOfCashFlows-direct",  # 341021 第一種中間連結キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_Type1SemiAnnualConsolidatedStatementOfCashFlows-direct",  # 341021 第一種中間連結キャッシュ・フロー計算書　直接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_QuarterlyConsolidatedStatementOfCashFlows-direct",  # 341030 四半期連結キャッシュ・フロー計算書　直接法（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_QuarterlyConsolidatedStatementOfCashFlows-direct",  # 341030 四半期連結キャッシュ・フロー計算書　直接法（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_ConsolidatedStatementOfCashFlows-indirect",  # 342010 連結キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_ConsolidatedStatementOfCashFlows-indirect",  # 342010 連結キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_SemiAnnualConsolidatedStatementOfCashFlows-indirect",  # 342020 第二種中間連結キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_SemiAnnualConsolidatedStatementOfCashFlows-indirect",  # 342020 第二種中間連結キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_Type1SemiAnnualConsolidatedStatementOfCashFlows-indirect",  # 342021 第一種中間連結キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_Type1SemiAnnualConsolidatedStatementOfCashFlows-indirect",  # 342021 第一種中間連結キャッシュ・フロー計算書　間接法
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_QuarterlyConsolidatedStatementOfCashFlows-indirect",  # 342030 四半期連結キャッシュ・フロー計算書　間接法（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_std_QuarterlyConsolidatedStatementOfCashFlows-indirect",  # 342030 四半期連結キャッシュ・フロー計算書　間接法（2025年版で廃止）
]

BS_ROLE_TYPE_IFRS = [
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_StatementOfFinancialPositionIFRS",  # 513040 財政状態計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedSemiAnnualStatementOfFinancialPositionIFRS",  # 513050 要約中間財政状態計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedQuarterlyStatementOfFinancialPositionIFRS",  # 513060 要約四半期財政状態計算書（IFRS）（2025年版で廃止）
]
CONSOLIDATED_BS_ROLE_TYPE_IFRS = [
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_ConsolidatedStatementOfFinancialPositionIFRS",  # 513010 連結財政状態計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_std_ConsolidatedStatementOfFinancialPositionIFRS",  # 513010 連結財政状態計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedSemiAnnualConsolidatedStatementOfFinancialPositionIFRS",  # 513020 要約中間連結財政状態計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedQuarterlyConsolidatedStatementOfFinancialPositionIFRS",  # 513030 要約四半期連結財政状態計算書（IFRS）（2025年版で廃止）
]

PL_ROLE_TYPE_IFRS = [
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_StatementOfProfitOrLossIFRS",  # 521040 損益計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedSemiAnnualStatementOfProfitOrLossIFRS",  # 521050 要約中間損益計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedYearToQuarterEndStatementOfProfitOrLossIFRS",  # 521061 要約四半期損益計算書（IFRS）四半期累計期間（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedQuarterPeriodStatementOfProfitOrLossIFRS",  # 521062 要約四半期損益計算書（IFRS）四半期会計期間（2025年版で廃止）
]
CONSOLIDATED_PL_ROLE_TYPE_IFRS = [
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_ConsolidatedStatementOfProfitOrLossIFRS",  # 521010 連結損益計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedSemiAnnualConsolidatedStatementOfProfitOrLossIFRS",  # 521020 要約中間連結損益計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedYearToQuarterEndConsolidatedStatementOfProfitOrLossIFRS",  # 521031 要約四半期連結損益計算書（IFRS）四半期累計期間（2025年版で廃止）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedQuarterPeriodConsolidatedStatementOfProfitOrLossIFRS",  # 521032 要約四半期連結損益計算書（IFRS）四半期会計期間（2025年版で廃止）
]
CF_ROLE_TYPE_IFRS = [
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_StatementOfCashFlowsIFRS",  # 540040 キャッシュ・フロー計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedSemiAnnualStatementOfCashFlowsIFRS",  # 540050 要約中間キャッシュ・フロー計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedQuarterlyStatementOfCashFlowsIFRS",  # 540060 要約四半期キャッシュ・フロー計算書（IFRS）（2025年版で廃止）
]
CONSOLIDATED_CF_ROLE_TYPE_IFRS = [
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_ConsolidatedStatementOfCashFlowsIFRS",  # 540010 連結キャッシュ・フロー計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_std_ConsolidatedStatementOfCashFlowsIFRS",  # 540010 連結キャッシュ・フロー計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedSemiAnnualConsolidatedStatementOfCashFlowsIFRS",  # 540020 要約中間連結キャッシュ・フロー計算書（IFRS）
    "http://disclosure.edinet-fsa.go.jp/role/jpigp/rol_CondensedQuarterlyConsolidatedStatementOfCashFlowsIFRS",  # 540030 要約四半期連結キャッシュ・フロー計算書（IFRS）（2025年版で廃止）
]


def _to_str_recursively(
    concept: ModelConcept,
    link_role: str,
    summation_item: str,
    depth: int = 0,
    suffix=None,
) -> str:
    parent_result = f"{'    ' * depth}{concept.label(lang='ja')} / {concept.label(lang='en')} / {concept.label(preferredLabel=XbrlConst.verboseLabel)} / {concept.qname} / {concept.balance}"
    if suffix:
        parent_result += f" / {suffix}"
    for relation in concept.modelXbrl.relationshipSet(
        summation_item, linkrole=link_role
    ).fromModelObject(concept):
        children_result = _to_str_recursively(
            relation.toModelObject,
            link_role=link_role,
            summation_item=summation_item,
            depth=depth + 1,
            suffix=f"weight = {relation.weight} / order = {relation.order}",
        )
        parent_result += f"\n{children_result}"
    return parent_result


def is_consolidated_fact(fact: ModelFact) -> bool:
    """
    EDINET は contextId に _NonConsolidatedMember が含まれている場合に非連結財務諸表として扱う
    [報告書インスタンス作成ガイドライン](https://www.fsa.go.jp/search/20241112/2b-1_InstanceGuide.pdf#41)
    """
    id = fact.contextID
    return "_NonConsolidatedMember" not in id


STANDARD_CONTEXT_ID_FIRST_ITEM = [
    "CurrentYear",
    "Interim",
    "Prior1Year",
    "Prior1Interim",
    "Prior2Year",
    "Prior2Interim",
    "Prior3Year",
    "Prior3Interim",
    "Prior4Year",
    "Prior4Interim",
    "Prior5Year",
    "Prior5Interim",
    "Prior6Year",
    "Prior6Interim",
    "Prior7Year",
    "Prior7Interim",
    "Prior8Year",
    "Prior8Interim",
]

STANDARD_CONTEXT_ID_SECOND_ITEM = [
    "Instant",
    "Duration",
]

STANDARD_CONTEXT_ID_THIRD_ITEM = [
    "",
    "_NonConsolidatedMember",
]

# [報告書インスタンス作成ガイドライン](https://www.fsa.go.jp/search/20241112/2b-1_InstanceGuide.pdf#41)
# 5-4-1 コンテキスト ID の命名規約 を参照
# Prior1YearInstant_jpcrp030000-asr_E00034-000RealEstateReportableSegmentsMember などと区別するためのリスト
STANDARD_CONTEXT_ID = [
    f"{first_item}{second_item}{third_item}"
    for first_item, second_item, third_item in product(
        STANDARD_CONTEXT_ID_FIRST_ITEM,
        STANDARD_CONTEXT_ID_SECOND_ITEM,
        STANDARD_CONTEXT_ID_THIRD_ITEM,
    )
]


def is_standard_context(context: ModelContext) -> bool:
    return context.id in STANDARD_CONTEXT_ID


def get_context_used_in_concept(
    concept: ModelConcept, consolidated: bool
) -> list[ModelContext]:
    model_xbrl = concept.modelXbrl
    facts = model_xbrl.factsByQname[concept.qname]
    contexts: set[ModelContext] = set()
    for fact in facts:
        if is_consolidated_fact(fact) != consolidated:
            continue
        if not is_standard_context(fact.context):
            continue
        contexts.add(fact.context)
    return list(contexts)


class AccountingItem(BaseModel):
    name: str
    nameJa: str | None
    nameEn: str | None
    nameDetail: str
    nameDetailJa: str | None
    nameDetailEn: str | None
    value: float
    items: list[Self]
    qname: str
    weight_in_parent: float | None = None
    order_in_parent: float | None = None
    balance: Literal["debit", "credit"] | None = None


class FinancialStatementConcept:
    InstanceType = TypeVar("InstanceType")

    def __init__(
        self,
        root_concepts: list[ModelConcept],
        role_type: str,
        summation_item: str,
        account_standard: str,
        consolidated: bool,
    ) -> Self:
        self.root_concepts = root_concepts
        self.role_type = role_type
        self.summation_item = summation_item
        self.account_standard = account_standard
        self.consolidated = consolidated
        self.contexts: list[ModelContext] = []

        if len(root_concepts) == 0:
            raise ValueError("Root concept should have at least 1 concept.")

        if root_concepts[0].modelXbrl is not None:
            self.xbrl_model: ModelXbrl = root_concepts[0].modelXbrl
        else:
            raise ValueError(
                f"ModelXbrl is not set in root_concepts[0]: {root_concepts[0]}"
            )

        contexts_used_in_each_root_concept: list[list[ModelContext]] = []
        for root_concept in root_concepts:
            contexts_used_in_root_concept = get_context_used_in_concept(
                root_concept, self.consolidated
            )
            contexts_used_in_each_root_concept.append(contexts_used_in_root_concept)

        # 株式会社ミツトヨの第105期半期決算では、BS の資産のルートコンセプトに紐づくコンテキストと負債純資産のルートコンセプトに紐づくコンテキストの集合が異なり、
        # 資産のほうにだけ、Prior1InterimInstant が入っている。PDF を見ても、実際にそうで、サマリーのところにPrior1InterimInstantの資産額だけ書いてある
        # これまでは、集合が完全に一致しないとエラーにしていたが、この事例によりコンテキストの集合の積をとることにした
        contexts_used_in_all_root_concepts = None
        for contexts_used_in_root_concept in contexts_used_in_each_root_concept:
            if contexts_used_in_all_root_concepts is None:
                contexts_used_in_all_root_concepts = set(contexts_used_in_root_concept)
            else:
                contexts_used_in_all_root_concepts = (
                    contexts_used_in_all_root_concepts
                    & set(contexts_used_in_root_concept)
                )

        if contexts_used_in_all_root_concepts is None:
            raise ValueError(
                f"Contexts used in all root concepts are not found, root_concepts: {root_concepts}"
            )

        self.contexts = list(contexts_used_in_all_root_concepts)

    @property
    def to_str_recursively(self) -> str:
        for root_concept in self.root_concepts:
            return _to_str_recursively(
                root_concept, self.role_type, self.summation_item
            )

    def _get_unique_fact_by_concept_and_context(
        self, concept: ModelConcept, context: ModelContext
    ) -> ModelFact:
        facts = self.xbrl_model.factsByQname[concept.qname]
        facts: list[ModelFact] = list(
            filter(lambda fact: fact.context == context, facts)
        )
        if len(facts) == 1:
            return facts[0]
        else:
            for fact_a, fact_b in combinations(facts, 2):
                if fact_a.sValue != fact_b.sValue:
                    raise ValueError(
                        f"Multiple facts with different values are found. facts: {facts}, context: {context}, concept: {concept}"
                    )
            return facts[0]

    def _get_to_child_relationship(
        self, parent_concept: ModelConcept
    ) -> list[ModelRelationship]:
        return self.xbrl_model.relationshipSet(
            self.summation_item, linkrole=self.role_type
        ).fromModelObject(parent_concept)

    def _get_child_concepts(
        self, parent_concept: ModelConcept
    ) -> list[tuple[ModelConcept, ModelRelationship]]:
        """
        Returns:
            list[tuple[ModelConcept, ModelRelationship]]: child_concepts と、親から子への関係のタプルのリスト
        """
        relationships = self._get_to_child_relationship(parent_concept)
        return [
            (relationship.toModelObject, relationship) for relationship in relationships
        ]

    def _extract_items(
        self,
        parent_concept: ModelConcept,
        context: ModelContext,
        relationship: ModelRelationship | None = None,
    ) -> AccountingItem | None:
        """
        context によって特定できる parent_concept 自身とその子孫の情報を再帰的に取得する
        """
        parent_fact = self._get_unique_fact_by_concept_and_context(
            parent_concept, context
        )
        if parent_fact.isNil:
            return None
        nameJa = parent_fact.concept.label(lang="ja")
        nameEn = parent_fact.concept.label(lang="en")
        nameDetailJa = parent_fact.concept.label(
            preferredLabel=XbrlConst.verboseLabel, lang="ja"
        )
        nameDetailEn = parent_fact.concept.label(
            preferredLabel=XbrlConst.verboseLabel, lang="en"
        )

        item = AccountingItem(
            nameJa=nameJa,
            nameEn=nameEn,
            nameDetailJa=nameDetailJa,
            nameDetailEn=nameDetailEn,
            name=nameJa or nameEn or parent_fact.concept.label(),
            nameDetail=nameDetailJa
            or nameDetailEn
            or parent_fact.concept.label(preferredLabel=XbrlConst.verboseLabel),
            value=parent_fact.xValue,
            items=[],
            qname=str(parent_fact.concept.qname),
            balance=parent_fact.concept.balance,
            weight_in_parent=relationship.weight if relationship is not None else None,
            order_in_parent=relationship.order if relationship is not None else None,
        )

        child_concepts = self._get_child_concepts(parent_concept)
        for child_concept, relationship in child_concepts:
            child_item = self._extract_items(child_concept, context, relationship)
            if child_item is not None:
                item.items.append(child_item)

        return item

    @staticmethod
    def search_unique_concept_by_qname_or_none(
        concepts: list[ModelConcept], qname: list[str]
    ) -> ModelConcept | None:
        """
        一つしかないと想定している concept を、その qname で検索する
        """
        searched_concepts: set[ModelConcept] = set()
        for concept in concepts:
            if str(concept.qname) in qname:
                searched_concepts.add(concept)
        if len(searched_concepts) == 1:
            return searched_concepts.pop()
        elif len(searched_concepts) > 1:
            raise ValueError(
                f"Multiple concepts are found. qname: {qname}, searched_concepts: {searched_concepts}"
            )
        else:
            return None

    @staticmethod
    def search_unique_concept_by_label(
        concepts: list[ModelConcept], words_in_label: list[str]
    ) -> ModelConcept | None:
        """
        一つしかないと想定している concept を、そのラベルに含まれる単語で検索する
        """
        searched_concepts: set[ModelConcept] = set()
        for concept in concepts:
            for search_word in words_in_label:
                if search_word in concept.label(lang="ja"):
                    searched_concepts.add(concept)
                elif search_word in concept.label(lang="en"):
                    searched_concepts.add(concept)
        if len(searched_concepts) == 1:
            return searched_concepts.pop()
        elif len(searched_concepts) > 1:
            raise ValueError(
                f"Multiple concepts are found. words_in_label: {words_in_label}, searched_concepts: {searched_concepts}"
            )
        else:
            return None

    @abstractmethod
    def extract_instances(self) -> list[InstanceType]:
        pass


class BSInstance(BaseModel):
    assets: AccountingItem
    liabilities: AccountingItem
    net_assets: AccountingItem
    consolidated: bool
    period: datetime
    unit: str
    roleType: str


class BSConcept(FinancialStatementConcept):
    def __init__(
        self,
        root_concepts: list[ModelConcept],
        role_type: str,
        summation_item: str,
        account_standard: str,
        consolidated: bool,
    ):
        super().__init__(
            root_concepts, role_type, summation_item, account_standard, consolidated
        )

        root_debit_concept: ModelConcept | None = None
        root_credit_concept: ModelConcept | None = None
        if len(root_concepts) != 2:
            raise ValueError("Root concept should have 2 concepts.")
        for root_concept in root_concepts:
            if root_concept.balance == "debit":
                root_debit_concept = root_concept
            elif root_concept.balance == "credit":
                root_credit_concept = root_concept

        if root_debit_concept is None and root_credit_concept is None:
            raise ValueError(
                f"Root concept should have debit or credit balance. root_concepts: {root_concepts}"
            )
        if root_debit_concept is None:
            raise ValueError(
                f"Root concept should have debit balance. root_concepts: {root_concepts}"
            )
        if root_credit_concept is None:
            raise ValueError(
                f"Root concept should have credit balance. root_concepts: {root_concepts}"
            )

        self.root_debit_concept = root_debit_concept
        self.root_credit_concept = root_credit_concept

    def extract_instances(self) -> list[BSInstance]:
        """
        contextRef ごとの貸借対照表のインスタンスを取得する
        """
        if len(self.root_concepts) == 0:
            return []
        instances: list[BSInstance] = []

        for context in self.contexts:
            assets = self._extract_items(self.root_debit_concept, context)
            credit_item = self._extract_items(self.root_credit_concept, context)

            debit_root_fact = self._get_unique_fact_by_concept_and_context(
                self.root_debit_concept, context
            )
            if len(credit_item.items) != 2:
                raise ValueError(
                    f"Credit item should have 2 items. credit_item: {credit_item}"
                )

            # 多分雑に順番で振り分けてしまって大丈夫
            liabilities = credit_item.items[0]
            net_assets = credit_item.items[1]

            instance = BSInstance(
                assets=assets,
                liabilities=liabilities,
                net_assets=net_assets,
                consolidated=self.consolidated,
                period=context.instantDatetime,
                unit=debit_root_fact.unitID,
                roleType=self.role_type,
            )
            instances.append(instance)

        return instances


type GET_FINANCIAL_STATEMENT_CONCEPT_ITEM = tuple[list[ModelConcept], str, str]


def _get_financial_statement_concepts(
    model_xbrl: ModelXbrl, role_types: list[str]
) -> list[GET_FINANCIAL_STATEMENT_CONCEPT_ITEM]:
    """
    財務諸表のConceptを取得する

    Parameters
    ----------
    model_xbrl : ModelXbrl
        XBRL のインスタンス
    role_types : list[str]
        財務諸表の roleType のリスト

    Returns
    -------
    list[list[ModelConcept], str, str]
        財務諸表のRoot Concept, roleType, summation_item_id のリスト
    """
    summation_items: list[ModelRelationshipSet] = []
    for summation_item_id in XbrlConst.summationItems:
        summation_item = model_xbrl.relationshipSet(summation_item_id)
        summation_items.append(summation_item)

    concepts: list[GET_FINANCIAL_STATEMENT_CONCEPT_ITEM] = []
    for summation_item in summation_items:
        for role_type in role_types:
            if role_type in summation_item.linkRoleUris.map:
                relationships = model_xbrl.relationshipSet(
                    summation_item.arcrole, linkrole=role_type
                )
                root_concepts: list[ModelConcept] = []
                for root_concept in relationships.rootConcepts:
                    root_concept: ModelConcept = root_concept
                    root_concepts.append(root_concept)
                concepts.append((root_concepts, role_type, summation_item.arcrole))

    return concepts


def _get_bs_jp_concepts(model_xbrl: ModelXbrl) -> list[BSConcept]:
    """
    JP GAAP の非連結貸借対照表のConceptを取得する
    """
    bs_jp_concepts = _get_financial_statement_concepts(model_xbrl, BS_ROLE_TYPE_JP)
    bs_concepts: list[BSConcept] = []
    for root_concepts, role_type, summation_item in bs_jp_concepts:
        bs_concept = BSConcept(
            root_concepts, role_type, summation_item, "JP GAAP", False
        )
        bs_concepts.append(bs_concept)
    return bs_concepts


def _get_bs_ifrs_concepts(model_xbrl: ModelXbrl) -> list[BSConcept]:
    """
    IFRS の非連結貸借対照表のConceptを取得する
    """
    bs_ifrs_concepts = _get_financial_statement_concepts(model_xbrl, BS_ROLE_TYPE_IFRS)
    bs_concepts: list[BSConcept] = []
    for root_concepts, role_type, summation_item in bs_ifrs_concepts:
        bs_concept = BSConcept(root_concepts, role_type, summation_item, "IFRS", False)
        bs_concepts.append(bs_concept)
    return bs_concepts


def _get_bs_consolidated_jp_concepts(model_xbrl: ModelXbrl) -> list[BSConcept]:
    """
    JP GAAP の連結貸借対照表のConceptを取得する
    """
    bs_consolidated_jp_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_BS_ROLE_TYPE_JP
    )
    bs_concepts: list[BSConcept] = []
    for root_concepts, role_type, summation_item in bs_consolidated_jp_concepts:
        bs_concept = BSConcept(
            root_concepts, role_type, summation_item, "JP GAAP", True
        )
        bs_concepts.append(bs_concept)
    return bs_concepts


def _get_bs_consolidated_ifrs_concepts(model_xbrl: ModelXbrl) -> list[BSConcept]:
    """
    IFRS の連結貸借対照表のConceptを取得する
    """
    bs_consolidated_ifrs_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_BS_ROLE_TYPE_IFRS
    )
    bs_concepts: list[BSConcept] = []
    for root_concepts, role_type, summation_item in bs_consolidated_ifrs_concepts:
        bs_concept = BSConcept(root_concepts, role_type, summation_item, "IFRS", True)
        bs_concepts.append(bs_concept)
    return bs_concepts


def get_bs_concepts(model_xbrl: ModelXbrl) -> list[BSConcept]:
    """
    貸借対照表のConceptを取得する
    """
    bs_jp_concepts = _get_bs_jp_concepts(model_xbrl)
    bs_ifrs_concepts = _get_bs_ifrs_concepts(model_xbrl)
    bs_consolidated_jp_concepts = _get_bs_consolidated_jp_concepts(model_xbrl)
    bs_consolidated_ifrs_concepts = _get_bs_consolidated_ifrs_concepts(model_xbrl)
    bs_concepts = (
        bs_jp_concepts
        + bs_ifrs_concepts
        + bs_consolidated_jp_concepts
        + bs_consolidated_ifrs_concepts
    )
    return bs_concepts


class PLInstance(BaseModel):
    # 営業利益
    operatingIncome: AccountingItem
    # 売上高（営業利益に対してプラスとするもの）
    netSales: list[AccountingItem]
    # 費用（営業利益に対してマイナスとするもの）
    expenses: list[AccountingItem]
    # 元の木構造をそのまま保持した、当期損益
    profitAndLoss: AccountingItem
    consolidated: bool
    durationFrom: datetime
    durationTo: datetime
    unit: str
    roleType: str


class PLConcept(FinancialStatementConcept):
    def __init__(
        self,
        root_concepts: list[ModelConcept],
        role_type: str,
        summation_item: str,
        account_standard: str,
        consolidated: bool,
    ):
        super().__init__(
            root_concepts, role_type, summation_item, account_standard, consolidated
        )

        pl_root_qnames = [
            "jppfs_cor:ProfitLoss",
            "jpigp_cor:ProfitLossIFRS",
        ]
        # root_concepts は一つを想定するが、一つとは限らない
        # 営業収益 / Operating revenue (jppfs_cor_OperatingRevenue1) が紛れることがある（cf. 高島屋157期（2022-2023））
        pl_root_concept = self.search_unique_concept_by_qname_or_none(
            root_concepts, pl_root_qnames
        )
        if pl_root_concept is None:
            # 一つも見つからない場合は、一つ下の階層を探す
            # たとえば、株式会社大盛工業の57期第2四半期決算は root_concept が包括利益（jppfs_cor:ComprehensiveIncome）で
            # その一つ下の階層に当期損益（jppfs_cor:ProfitLoss）がある
            root_child_concepts: list[ModelConcept] = []
            for root_concept in root_concepts:
                root_child_concepts_and_relationship = self._get_child_concepts(
                    root_concept
                )
                for root_child_concept, _ in root_child_concepts_and_relationship:
                    root_child_concepts.append(root_child_concept)
            pl_root_concept = self.search_unique_concept_by_qname_or_none(
                root_child_concepts, pl_root_qnames
            )

        # for root_concept in root_concepts:
        #     print(_to_str_recursively(root_concept, role_type, summation_item))

        if pl_root_concept is None:
            raise ValueError(
                f"Profit and loss root concept should be found, root_concepts: {root_concepts}"
            )
        self.pl_root_concept = pl_root_concept

    def _is_decendant_items_weight_all_one(self, current_item: AccountingItem) -> bool:
        """
        items を再帰的に深さ優先で調べて、全ての items の weight が 1 であるかどうかを返す
        本来ならメモ化再帰で実装するべきだが、items の数が多くないので、単純な再帰で実装
        """
        if len(current_item.items) == 0:
            return True
        if all(item.weight_in_parent == 1 for item in current_item.items):
            return all(
                self._is_decendant_items_weight_all_one(item)
                for item in current_item.items
            )
        else:
            return False

    def _is_decendant_items_balance_all_same(
        self, balance: Literal["debit", "credit"], current_item: AccountingItem
    ) -> bool:
        """
        自身とその子孫を再帰的に深さ優先で調べて、全ての items の balance が balance であるかどうかを返す
        本来ならメモ化再帰で実装するべきだが、items の数が多くないので、単純な再帰で実装
        """
        if current_item.balance != balance:
            return False
        return all(
            self._is_decendant_items_balance_all_same(balance, item)
            for item in current_item.items
        )

    def _get_qname_item_recursively(
        self, current_item: AccountingItem, qname: list[str]
    ) -> AccountingItem | None:
        """
        items を再帰的に深さ優先で調べて、qname のいずれかが一致する AccountingItem を返す
        """
        if current_item.qname in qname:
            return current_item
        for item in current_item.items:
            result = self._get_qname_item_recursively(item, qname)
            if result is not None:
                return result

    def _extract_operating_income(
        self, parent_item: AccountingItem
    ) -> AccountingItem | None:
        """
        parent_item を再帰的に辿って、営業利益を取得する
        """
        operating_income_qnames = [
            "jppfs_cor:OperatingIncome",
            "jpigp_cor:OperatingProfitLossIFRS",
        ]

        operating_income_item = self._get_qname_item_recursively(
            parent_item, operating_income_qnames
        )

        if operating_income_item is not None:
            return operating_income_item

        # 銀行の場合を考慮
        # 銀行の場合は営業利益という概念が慣例的になく、経常利益（OrdinaryIncome）を営業利益として扱う
        operating_income_bnk_item = self._extract_ordinaly_income_bnk(parent_item)
        if operating_income_bnk_item is not None:
            return operating_income_bnk_item

        return None

    def _extract_ordinaly_income_bnk(
        self, parent_item: AccountingItem
    ) -> AccountingItem | None:
        """
        銀行の場合は営業利益という概念が慣例的にない
        [やさしい銀行の読み方 全国銀行協会](https://www.zenginkyo.or.jp/fileadmin/res/abstract/efforts/smooth/accounting/disclosure.pdf#page=18)
        そのため、子孫に jppfs_cor:OrdinaryIncomeBNK があれば、jppfs_cor:OrdinaryIncome を営業利益として扱う
        """
        operating_income_qnames = [
            "jppfs_cor:OrdinaryIncome",
        ]
        operating_income_item = self._get_qname_item_recursively(
            parent_item, operating_income_qnames
        )

        if operating_income_item is None:
            return None

        # 子孫に jppfs_cor:OrdinaryIncomeBNK などの銀行を示す項目がない場合は、営業利益として扱うことはできない
        operating_income_bnk_qnames = [
            "jppfs_cor:OrdinaryIncomeBNK",
            "jppfs_cor:OrdinaryExpensesBNK",
        ]
        operating_income_bnk_item = self._get_qname_item_recursively(
            operating_income_item, operating_income_bnk_qnames
        )

        if operating_income_bnk_item is None:
            return None

        return operating_income_item

    def _extract_expenses_and_net_sales(
        self, operating_income: AccountingItem
    ) -> tuple[list[AccountingItem], list[AccountingItem]]:
        """
        operating_income を再帰的に辿って、費用と売上高を取得する
        expenses は、自身と子孫の balance が debit のもの
        net_sales は、自身と子孫の balance が credit のもの

        Returns:
            tuple[list[AccountingItem], list[AccountingItem]]: first item is expenses, second item is net sales
        """

        def extract_expenses_and_net_sales_recursively(
            current_item: AccountingItem,
            expenses: list[AccountingItem],
            net_sales: list[AccountingItem],
        ) -> tuple[list[AccountingItem], list[AccountingItem]]:
            if self._is_decendant_items_balance_all_same("debit", current_item):
                expenses.append(current_item)
                return expenses, net_sales
            elif self._is_decendant_items_balance_all_same("credit", current_item):
                net_sales.append(current_item)
                return expenses, net_sales
            for item in current_item.items:
                expenses, net_sales = extract_expenses_and_net_sales_recursively(
                    item, expenses, net_sales
                )
            return expenses, net_sales

        expenses, net_sales = extract_expenses_and_net_sales_recursively(
            operating_income, [], []
        )
        return expenses, net_sales

    def extract_instances(self) -> list[PLInstance]:
        """
        contextRef ごとの損益計算書のインスタンスを取得する
        """
        instances: list[PLInstance] = []

        for context in self.contexts:
            pl_root_fact = self._get_unique_fact_by_concept_and_context(
                self.pl_root_concept, context
            )
            profit_and_loss_item = self._extract_items(self.pl_root_concept, context)
            if profit_and_loss_item is None:
                raise ValueError(
                    f"Profit and loss item should not be None. context: {context}, pl_root_concept: {self.pl_root_concept}"
                )

            # 営業利益を起点とする
            operating_income_item = self._extract_operating_income(profit_and_loss_item)
            if operating_income_item is None:
                raise ValueError(
                    f"Operating income item should not be None. context: {context}, pl_root_concept: {self.pl_root_concept}"
                )

            expenses, net_sales = self._extract_expenses_and_net_sales(
                operating_income_item
            )

            instance = PLInstance(
                operatingIncome=operating_income_item,
                expenses=expenses,
                netSales=net_sales,
                profitAndLoss=profit_and_loss_item,
                consolidated=self.consolidated,
                durationFrom=context.startDatetime,
                durationTo=context.endDatetime,
                unit=pl_root_fact.unitID,
                roleType=self.role_type,
            )
            instances.append(instance)

        return instances


def _get_pl_jp_concepts(model_xbrl: ModelXbrl) -> list[PLConcept]:
    """
    JP GAAP の非連結損益計算書のConceptを取得する
    """
    pl_jp_concepts = _get_financial_statement_concepts(model_xbrl, PL_ROLE_TYPE_JP)
    pl_concepts: list[PLConcept] = []
    for root_concepts, role_type, summation_item in pl_jp_concepts:
        pl_concept = PLConcept(
            root_concepts, role_type, summation_item, "JP GAAP", False
        )
        pl_concepts.append(pl_concept)
    return pl_concepts


def _get_pl_ifrs_concepts(model_xbrl: ModelXbrl) -> list[PLConcept]:
    """
    IFRS の非連結損益計算書のConceptを取得する
    """
    pl_ifrs_concepts = _get_financial_statement_concepts(model_xbrl, PL_ROLE_TYPE_IFRS)
    pl_concepts: list[PLConcept] = []
    for root_concepts, role_type, summation_item in pl_ifrs_concepts:
        pl_concept = PLConcept(root_concepts, role_type, summation_item, "IFRS", False)
        pl_concepts.append(pl_concept)
    return pl_concepts


def _get_pl_consolidated_jp_concepts(model_xbrl: ModelXbrl) -> list[PLConcept]:
    """
    JP GAAP の連結損益計算書のConceptを取得する
    """
    pl_consolidated_jp_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_PL_ROLE_TYPE_JP
    )
    pl_concepts: list[PLConcept] = []
    for root_concepts, role_type, summation_item in pl_consolidated_jp_concepts:
        pl_concept = PLConcept(
            root_concepts, role_type, summation_item, "JP GAAP", True
        )
        pl_concepts.append(pl_concept)
    return pl_concepts


def _get_pl_consolidated_ifrs_concepts(model_xbrl: ModelXbrl) -> list[PLConcept]:
    """
    IFRS の連結損益計算書のConceptを取得する
    """
    pl_consolidated_ifrs_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_PL_ROLE_TYPE_IFRS
    )
    pl_concepts: list[PLConcept] = []
    for root_concepts, role_type, summation_item in pl_consolidated_ifrs_concepts:
        pl_concept = PLConcept(root_concepts, role_type, summation_item, "IFRS", True)
        pl_concepts.append(pl_concept)
    return pl_concepts


def get_pl_concepts(model_xbrl: ModelXbrl) -> list[PLConcept]:
    """
    損益計算書のConceptを取得する
    """
    pl_jp_concepts = _get_pl_jp_concepts(model_xbrl)
    pl_ifrs_concepts = _get_pl_ifrs_concepts(model_xbrl)
    pl_consolidated_jp_concepts = _get_pl_consolidated_jp_concepts(model_xbrl)
    pl_consolidated_ifrs_concepts = _get_pl_consolidated_ifrs_concepts(model_xbrl)
    pl_concepts = (
        pl_jp_concepts
        + pl_ifrs_concepts
        + pl_consolidated_jp_concepts
        + pl_consolidated_ifrs_concepts
    )
    return pl_concepts


class CFInstance(BaseModel):
    operating: AccountingItem
    investing: AccountingItem
    financing: AccountingItem
    consolidated: bool
    durationFrom: datetime
    durationTo: datetime
    unit: str
    roleType: str


class CFConcept(FinancialStatementConcept):
    def __init__(
        self,
        root_concepts: list[ModelConcept],
        role_type: str,
        summation_item: str,
        account_standard: str,
        consolidated: bool,
    ):
        super().__init__(
            root_concepts, role_type, summation_item, account_standard, consolidated
        )

        if len(root_concepts) != 1:
            raise ValueError(
                f"Root concept should have at least 1 concept, but got {len(root_concepts)}, root_concepts: {root_concepts}"
            )
        main_concepts_and_relationship = self._get_child_concepts(root_concepts[0])
        main_concepts = [concept for concept, _ in main_concepts_and_relationship]

        # オリックス銀行株式会社第32期半期決算書には、財務活動キャッシュフローがない
        # キャッシュフローは必ずしも三つが全て揃っているわけではないため、None を許容する
        root_operating_concept: ModelConcept | None = (
            self.search_unique_concept_by_label(
                main_concepts, ["営業活動", "operating"]
            )
        )
        root_investing_concept: ModelConcept | None = (
            self.search_unique_concept_by_label(
                main_concepts, ["投資活動", "investing"]
            )
        )
        root_financing_concept: ModelConcept | None = (
            self.search_unique_concept_by_label(
                main_concepts, ["財務活動", "financing"]
            )
        )

        if root_operating_concept is None:
            print(
                f"[WARNING] Operating concept is not found. main_concepts: {main_concepts}"
            )

        if root_investing_concept is None:
            print(
                f"[WARNING] Investing concept is not found. main_concepts: {main_concepts}"
            )

        if root_financing_concept is None:
            print(
                f"[WARNING] Financing concept is not found. main_concepts: {main_concepts}"
            )

        self.root_operating_concept: ModelConcept | None = root_operating_concept
        self.root_investing_concept: ModelConcept | None = root_investing_concept
        self.root_financing_concept: ModelConcept | None = root_financing_concept

    def extract_instances(self) -> list[CFInstance]:
        """
        contextRef ごとのキャッシュフロー計算書のインスタンスを取得する
        """
        if len(self.root_concepts) == 0:
            return []
        instances: list[CFInstance] = []

        placeholder_accounting_item = AccountingItem(
            nameJa="N/A",
            nameEn="N/A",
            nameDetailJa="該当するキャッシュフロー計算書の項目が見つかりませんでした",
            nameDetailEn="No item found in the cash flow statement",
            name="N/A",
            nameDetail="該当するキャッシュフロー計算書の項目が見つかりませんでした",
            value=0.0,
            items=[],
            qname="N/A",
            balance=None,
            weight_in_parent=None,
            order_in_parent=None,
        )

        for context in self.contexts:
            # 対応する concept がない場合や、対応する concept があっても対応する fact がない場合は、placeholder_accounting_item を使う
            operating_item = None
            if self.root_operating_concept is not None:
                operating_item = self._extract_items(
                    self.root_operating_concept, context
                )
            if operating_item is None:
                operating_item = placeholder_accounting_item

            investing_item = None
            if self.root_investing_concept is not None:
                investing_item = self._extract_items(
                    self.root_investing_concept, context
                )
            if investing_item is None:
                investing_item = placeholder_accounting_item

            financing_item = None
            if self.root_financing_concept is not None:
                financing_item = self._extract_items(
                    self.root_financing_concept, context
                )
            if financing_item is None:
                financing_item = placeholder_accounting_item

            operating_root_fact = self._get_unique_fact_by_concept_and_context(
                self.root_operating_concept, context
            )
            duration_from = context.startDatetime
            duration_to = context.endDatetime

            instance = CFInstance(
                operating=operating_item,
                investing=investing_item,
                financing=financing_item,
                consolidated=self.consolidated,
                durationFrom=duration_from,
                durationTo=duration_to,
                unit=operating_root_fact.unitID,
                roleType=self.role_type,
            )
            instances.append(instance)

        return instances


def _get_cf_jp_concepts(model_xbrl: ModelXbrl) -> list[CFConcept]:
    """
    JP GAAP の非連結キャッシュフロー計算書のConceptを取得する
    """
    cf_jp_concepts = _get_financial_statement_concepts(model_xbrl, CF_ROLE_TYPE_JP)
    cf_concepts: list[CFConcept] = []
    for root_concepts, role_type, summation_item in cf_jp_concepts:
        cf_concept = CFConcept(
            root_concepts, role_type, summation_item, "JP GAAP", False
        )
        cf_concepts.append(cf_concept)
    return cf_concepts


def _get_cf_ifrs_concepts(model_xbrl: ModelXbrl) -> list[CFConcept]:
    """
    IFRS の非連結キャッシュフロー計算書のConceptを取得する
    """
    cf_ifrs_concepts = _get_financial_statement_concepts(model_xbrl, CF_ROLE_TYPE_IFRS)
    cf_concepts: list[CFConcept] = []
    for root_concepts, role_type, summation_item in cf_ifrs_concepts:
        cf_concept = CFConcept(root_concepts, role_type, summation_item, "IFRS", False)
        cf_concepts.append(cf_concept)
    return cf_concepts


def _get_cf_consolidated_jp_concepts(model_xbrl: ModelXbrl) -> list[CFConcept]:
    """
    JP GAAP の連結キャッシュフロー計算書のConceptを取得する
    """
    cf_consolidated_jp_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_CF_ROLE_TYPE_JP
    )
    cf_concepts: list[CFConcept] = []
    for root_concepts, role_type, summation_item in cf_consolidated_jp_concepts:
        cf_concept = CFConcept(
            root_concepts, role_type, summation_item, "JP GAAP", True
        )
        cf_concepts.append(cf_concept)
    return cf_concepts


def _get_cf_consolidated_ifrs_concepts(model_xbrl: ModelXbrl) -> list[CFConcept]:
    """
    IFRS の連結キャッシュフロー計算書のConceptを取得する
    """
    cf_consolidated_ifrs_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_CF_ROLE_TYPE_IFRS
    )
    cf_concepts: list[CFConcept] = []
    for root_concepts, role_type, summation_item in cf_consolidated_ifrs_concepts:
        cf_concept = CFConcept(root_concepts, role_type, summation_item, "IFRS", True)
        cf_concepts.append(cf_concept)
    return cf_concepts


def get_cf_concepts(model_xbrl: ModelXbrl) -> list[CFConcept]:
    """
    キャッシュフロー計算書のConceptを取得する
    """
    cf_jp_concepts = _get_cf_jp_concepts(model_xbrl)
    cf_ifrs_concepts = _get_cf_ifrs_concepts(model_xbrl)
    cf_consolidated_jp_concepts = _get_cf_consolidated_jp_concepts(model_xbrl)
    cf_consolidated_ifrs_concepts = _get_cf_consolidated_ifrs_concepts(model_xbrl)
    cf_concepts = (
        cf_jp_concepts
        + cf_ifrs_concepts
        + cf_consolidated_jp_concepts
        + cf_consolidated_ifrs_concepts
    )
    return cf_concepts
