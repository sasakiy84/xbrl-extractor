from pathlib import Path
from zipfile import ZipFile
from arelle import Cntlr, FileSource
from arelle.ModelXbrl import ModelXbrl
from arelle.ModelDtsObject import ModelConcept
from arelle import XbrlConst
from arelle.ModelRelationshipSet import ModelRelationshipSet


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
    concept: ModelConcept, link_role: str, summation_item: str, depth: int = 0
) -> str:
    partent_result = f"{'    ' * depth}{concept.label()} / {concept.label(lang='en')} / {concept.label(preferredLabel=XbrlConst.verboseLabel)}"
    for relation in concept.modelXbrl.relationshipSet(
        summation_item, linkrole=link_role
    ).fromModelObject(concept):
        child_result = _to_str_recursively(
            relation.toModelObject,
            link_role=link_role,
            summation_item=summation_item,
            depth=depth + 1,
        )
        partent_result += f"\n{child_result}"
    return partent_result


class FinancialStatementConcept:
    def __init__(
        self,
        concept: ModelConcept,
        role_type: str,
        summation_item: str,
        account_standard: str,
        consolidated: bool,
    ):
        self.concept = concept
        self.role_type = role_type
        self.summation_item = summation_item
        self.account_standard = account_standard
        self.consolidated = consolidated

    @property
    def to_str_recursively(self):
        return _to_str_recursively(self.concept, self.role_type, self.summation_item)


class BSConcept(FinancialStatementConcept):
    def __init__(
        self,
        concept: ModelConcept,
        role_type: str,
        summation_item: str,
        account_standard: str,
        consolidated: bool,
    ):
        super().__init__(
            concept, role_type, summation_item, account_standard, consolidated
        )


def _get_financial_statement_concepts(
    model_xbrl: ModelXbrl, role_types: list[str]
) -> list[ModelConcept]:
    """
    財務諸表のConceptを取得する
    """
    summation_items: list[ModelRelationshipSet] = []
    for summation_item_id in XbrlConst.summationItems:
        summation_item = model_xbrl.relationshipSet(summation_item_id)
        summation_items.append(summation_item)

    root_concepts: list[tuple[ModelConcept, str, str]] = []
    for summation_item in summation_items:
        for role_type in role_types:
            if role_type in summation_item.linkRoleUris.map:
                relationships = model_xbrl.relationshipSet(
                    summation_item.arcrole, linkrole=role_type
                )
                for root_concept in relationships.rootConcepts:
                    root_concept: ModelConcept = root_concept
                    root_concepts.append(
                        (root_concept, role_type, summation_item.arcrole)
                    )

    return root_concepts


def _get_bs_jp_concepts(model_xbrl: ModelXbrl) -> list[BSConcept]:
    """
    JP GAAP の非連結貸借対照表のConceptを取得する
    """
    bs_jp_root_concepts = _get_financial_statement_concepts(model_xbrl, BS_ROLE_TYPE_JP)
    bs_concepts: list[BSConcept] = []
    for concept, role_type, summation_item in bs_jp_root_concepts:
        bs_concept = BSConcept(concept, role_type, summation_item, "JP GAAP", False)
        bs_concepts.append(bs_concept)
    return bs_concepts


def _get_bs_ifrs_concepts(model_xbrl: ModelXbrl) -> list[BSConcept]:
    """
    IFRS の非連結貸借対照表のConceptを取得する
    """
    bs_ifrs_root_concepts = _get_financial_statement_concepts(
        model_xbrl, BS_ROLE_TYPE_IFRS
    )
    bs_concepts: list[BSConcept] = []
    for concept, role_type, summation_item in bs_ifrs_root_concepts:
        bs_concept = BSConcept(concept, role_type, summation_item, "IFRS", False)
        bs_concepts.append(bs_concept)
    return bs_concepts


def _get_bs_consolidated_jp_concepts(model_xbrl: ModelXbrl) -> list[BSConcept]:
    """
    JP GAAP の連結貸借対照表のConceptを取得する
    """
    bs_consolidated_jp_root_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_BS_ROLE_TYPE_JP
    )
    bs_concepts: list[BSConcept] = []
    for concept, role_type, summation_item in bs_consolidated_jp_root_concepts:
        bs_concept = BSConcept(concept, role_type, summation_item, "JP GAAP", True)
        bs_concepts.append(bs_concept)
    return bs_concepts


def _get_bs_consolidated_ifrs_concepts(model_xbrl: ModelXbrl) -> list[BSConcept]:
    """
    IFRS の連結貸借対照表のConceptを取得する
    """
    bs_consolidated_ifrs_root_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_BS_ROLE_TYPE_IFRS
    )
    bs_concepts: list[BSConcept] = []
    for concept, role_type, summation_item in bs_consolidated_ifrs_root_concepts:
        bs_concept = BSConcept(concept, role_type, summation_item, "IFRS", True)
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


class PLConcept(FinancialStatementConcept):
    def __init__(
        self,
        concept: ModelConcept,
        role_type: str,
        summation_item: str,
        account_standard: str,
        consolidated: bool,
    ):
        super().__init__(
            concept, role_type, summation_item, account_standard, consolidated
        )


def _get_pl_jp_concepts(model_xbrl: ModelXbrl) -> list[PLConcept]:
    """
    JP GAAP の非連結損益計算書のConceptを取得する
    """
    pl_jp_root_concepts = _get_financial_statement_concepts(model_xbrl, PL_ROLE_TYPE_JP)
    pl_concepts: list[PLConcept] = []
    for concept, role_type, summation_item in pl_jp_root_concepts:
        pl_concept = PLConcept(concept, role_type, summation_item, "JP GAAP", False)
        pl_concepts.append(pl_concept)
    return pl_concepts


def _get_pl_ifrs_concepts(model_xbrl: ModelXbrl) -> list[PLConcept]:
    """
    IFRS の非連結損益計算書のConceptを取得する
    """
    pl_ifrs_root_concepts = _get_financial_statement_concepts(
        model_xbrl, PL_ROLE_TYPE_IFRS
    )
    pl_concepts: list[PLConcept] = []
    for concept, role_type, summation_item in pl_ifrs_root_concepts:
        pl_concept = PLConcept(concept, role_type, summation_item, "IFRS", False)
        pl_concepts.append(pl_concept)
    return pl_concepts


def _get_pl_consolidated_jp_concepts(model_xbrl: ModelXbrl) -> list[PLConcept]:
    """
    JP GAAP の連結損益計算書のConceptを取得する
    """
    pl_consolidated_jp_root_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_PL_ROLE_TYPE_JP
    )
    pl_concepts: list[PLConcept] = []
    for concept, role_type, summation_item in pl_consolidated_jp_root_concepts:
        pl_concept = PLConcept(concept, role_type, summation_item, "JP GAAP", True)
        pl_concepts.append(pl_concept)
    return pl_concepts


def _get_pl_consolidated_ifrs_concepts(model_xbrl: ModelXbrl) -> list[PLConcept]:
    """
    IFRS の連結損益計算書のConceptを取得する
    """
    pl_consolidated_ifrs_root_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_PL_ROLE_TYPE_IFRS
    )
    pl_concepts: list[PLConcept] = []
    for concept, role_type, summation_item in pl_consolidated_ifrs_root_concepts:
        pl_concept = PLConcept(concept, role_type, summation_item, "IFRS", True)
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


class CFConcept(FinancialStatementConcept):
    def __init__(
        self,
        concept: ModelConcept,
        role_type: str,
        summation_item: str,
        account_standard: str,
        consolidated: bool,
    ):
        super().__init__(
            concept, role_type, summation_item, account_standard, consolidated
        )


def _get_cf_jp_concepts(model_xbrl: ModelXbrl) -> list[CFConcept]:
    """
    JP GAAP の非連結キャッシュフロー計算書のConceptを取得する
    """
    cf_jp_root_concepts = _get_financial_statement_concepts(model_xbrl, CF_ROLE_TYPE_JP)
    cf_concepts: list[CFConcept] = []
    for concept, role_type, summation_item in cf_jp_root_concepts:
        cf_concept = CFConcept(concept, role_type, summation_item, "JP GAAP", False)
        cf_concepts.append(cf_concept)
    return cf_concepts


def _get_cf_ifrs_concepts(model_xbrl: ModelXbrl) -> list[CFConcept]:
    """
    IFRS の非連結キャッシュフロー計算書のConceptを取得する
    """
    cf_ifrs_root_concepts = _get_financial_statement_concepts(
        model_xbrl, CF_ROLE_TYPE_IFRS
    )
    cf_concepts: list[CFConcept] = []
    for concept, role_type, summation_item in cf_ifrs_root_concepts:
        cf_concept = CFConcept(concept, role_type, summation_item, "IFRS", False)
        cf_concepts.append(cf_concept)
    return cf_concepts


def _get_cf_consolidated_jp_concepts(model_xbrl: ModelXbrl) -> list[CFConcept]:
    """
    JP GAAP の連結キャッシュフロー計算書のConceptを取得する
    """
    cf_consolidated_jp_root_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_CF_ROLE_TYPE_JP
    )
    cf_concepts: list[CFConcept] = []
    for concept, role_type, summation_item in cf_consolidated_jp_root_concepts:
        cf_concept = CFConcept(concept, role_type, summation_item, "JP GAAP", True)
        cf_concepts.append(cf_concept)
    return cf_concepts


def _get_cf_consolidated_ifrs_concepts(model_xbrl: ModelXbrl) -> list[CFConcept]:
    """
    IFRS の連結キャッシュフロー計算書のConceptを取得する
    """
    cf_consolidated_ifrs_root_concepts = _get_financial_statement_concepts(
        model_xbrl, CONSOLIDATED_CF_ROLE_TYPE_IFRS
    )
    cf_concepts: list[CFConcept] = []
    for concept, role_type, summation_item in cf_consolidated_ifrs_root_concepts:
        cf_concept = CFConcept(concept, role_type, summation_item, "IFRS", True)
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
