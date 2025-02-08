export type ReponseMetadata = {
	title: string;
	parameter: Parameter;
	resultset: Resultset;
	processDateTime: string;
	status: "200" | "400" | "401" | "404" | "500";
	message: string;
};

export type Parameter = {
	date: string;
	type: "1" | "2";
};

export type Resultset = {
	count: number;
};

export type DocumentMetadata = {
	seqNumber: number;
	docID: string;
	edinetCode: string;
	secCode: string | null;
	JCN: string;
	filerName: string;
	fundCode: string | null;
	ordinanceCode: string;
	formCode: string;
	docTypeCode: DocTypeCode;
	periodStart: string | null;
	periodEnd: string | null;
	submitDateTime: string;
	docDescription: string;
	issuerEdinetCode: string | null;
	subjectEdinetCode: string | null;
	subsidiaryEdinetCode: string | null;
	currentReportReason: string | null;
	parentDocID: string | null;
	opeDateTime: string | null;
	withdrawalStatus: "0" | "1";
	docInfoEditStatus: "0" | "1";
	disclosureStatus: "0" | "1";
	xbrlFlag: "0" | "1";
	pdfFlag: "0" | "1";
	attachDocFlag: "0" | "1";
	englishDocFlag: "0" | "1";
	csvFlag: "0" | "1";
	legalStatus: "0" | "1";
};

export type ListResponse = {
	metadata: ReponseMetadata;
	results: DocumentMetadata[];
};

type DocTypeCode =
	| "010" // 有価証券通知書
	| "020" // 変更通知書(有価証券通知書)
	| "030" // 有価証券届出書
	| "040" // 訂正有価証券届出書
	| "050" // 届出の取下げ願い
	| "060" // 発行登録通知書
	| "070" // 変更通知書(発行登録通知書)
	| "080" // 発行登録書
	| "090" // 訂正発行登録書
	| "100" // 発行登録追補書類
	| "110" // 発行登録取下届出書
	| "120" // 有価証券報告書
	| "130" // 訂正有価証券報告書
	| "135" // 確認書
	| "136" // 訂正確認書
	| "140" // 四半期報告書
	| "150" // 訂正四半期報告書
	| "160" // 半期報告書
	| "170" // 訂正半期報告書
	| "180" // 臨時報告書
	| "190" // 訂正臨時報告書
	| "200" // 親会社等状況報告書
	| "210" // 訂正親会社等状況報告書
	| "220" // 自己株券買付状況報告書
	| "230" // 訂正自己株券買付状況報告書
	| "235" // 内部統制報告書
	| "236" // 訂正内部統制報告書
	| "240" // 公開買付届出書
	| "250" // 訂正公開買付届出書
	| "260" // 公開買付撤回届出書
	| "270" // 公開買付報告書
	| "280" // 訂正公開買付報告書
	| "290" // 意見表明報告書
	| "300" // 訂正意見表明報告書
	| "310" // 対質問回答報告書
	| "320" // 訂正対質問回答報告書
	| "330" // 別途買付け禁止の特例を受けるための申出書
	| "340" // 訂正別途買付け禁止の特例を受けるための申出書
	| "350" // 大量保有報告書
	| "360" // 訂正大量保有報告書
	| "370" // 基準日の届出書
	| "380" // 変更の届出書
	| null;
