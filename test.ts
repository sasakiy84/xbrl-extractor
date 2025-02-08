import type { DocumentMetadata, ListResponse } from "./types.ts";
// import path lib
import { join } from "jsr:@std/path";

const EDINET_ENDPOINT_V2 = Deno.env.get("EDINET_ENDPOINT_V2");
const API_KEY = Deno.env.get("EDINET_API_KEY");

if (EDINET_ENDPOINT_V2 === undefined) {
	throw new Error("EDINET_ENDPOINT_V2 is not set");
}
if (API_KEY === undefined) {
	throw new Error("EDINET_API_KEY is not set");
}

/**
 * 1日分の提出書類一覧を取得する。
 * type 1 はメタデータのみを取得。
 * type 2 は提出書類一覧及びメタデータを取得。
 */
const listDocumentsPerDate = async ({
	type = "2",
	date = new Date(),
}: {
	type?: "1" | "2";
	date?: Date;
}): Promise<ListResponse> => {
	const urlParams = new URLSearchParams({
		type,
		date: date.toISOString().split("T")[0],
		"Subscription-Key": API_KEY,
	});
	const path = `documents.json?${urlParams}`;
	const url = new URL(path, EDINET_ENDPOINT_V2);
	const response = await fetch(url);
	return response.json();
};

/**
 * 指定した書類IDの提出書類をダウンロードする。
 * type 1 は提出本文書及び監査報告書を取得(提出書類本文(外国会社の英文報告本文は除く)に加えて、監査報告書、あれば XBRLファイル)。（ZIP形式）
 * type 2 はPDFを取得（PDF形式）。
 * type 3 は代替書面・添付文書を取得（ZIP形式）。
 * type 4 は英文ファイルを取得（ZIP形式）。
 * type 5 はCSVを取得（ZIP形式）。
 */
const downloadDocuments = async ({
	documentId,
	type,
}: {
	documentId: string;
	type: "1" | "2" | "3" | "4" | "5";
}): Promise<Response> => {
	const urlParams = new URLSearchParams({
		type,
		"Subscription-Key": API_KEY,
	});
	const url = new URL(
		`documents/${documentId}?${urlParams}`,
		EDINET_ENDPOINT_V2,
	);
	const response = await fetch(url);
	return response;
};

/**
 * 指定した書類IDのXBRLファイルをダウンロードして、指定したフォルダに保存する。
 */
const downloadXBRL = async (documentId: string, resultPath: string) => {
	const response = await downloadDocuments({
		documentId,
		type: "1",
	});
	const blob = await response.blob();
	await Deno.writeFile(resultPath, new Uint8Array(await blob.arrayBuffer()));
};

const downloadPDF = async (documentId: string, resultPath: string) => {
	const response = await downloadDocuments({
		documentId,
		type: "2",
	});
	const blob = await response.blob();
	await Deno.writeFile(resultPath, new Uint8Array(await blob.arrayBuffer()));
};

const downloadCSV = async (documentId: string, resultPath: string) => {
	const response = await downloadDocuments({
		documentId,
		type: "5",
	});
	const blob = await response.blob();
	await Deno.writeFile(resultPath, new Uint8Array(await blob.arrayBuffer()));
};

const results: DocumentMetadata[] = [];
const DATE_RANGE = {
	from: new Date("2022-01-01"),
	to: new Date("2024-12-31"),
};

for (
	const date = DATE_RANGE.from;
	date <= DATE_RANGE.to;
	date.setDate(date.getDate() + 1)
) {
	console.info(`Fetching documents for ${date.toISOString().split("T")[0]}`);
	const result = await listDocumentsPerDate({ date });
	const periodicalReportMetadata = result.results
		.filter(
			// 有価証券通知書、四半期報告書、半期報告書
			(doc) =>
				doc.docTypeCode === "120" ||
				doc.docTypeCode === "140" ||
				doc.docTypeCode === "160",
		)
		.filter(
			// fund 関係の書類は除外
			(doc) => doc.fundCode === null,
		);
	results.push(...periodicalReportMetadata);
	await new Promise((resolve) => setTimeout(resolve, 10));
}

// save to file
Deno.writeTextFile("documents.json", JSON.stringify(results, null, 2));

const docTypeCodeToName = (docTypeCode: string): string | undefined => {
	const docTypeCodeToName: Record<string, string> = {
		"120": "有価証券報告書",
		"140": "四半期報告書",
		"160": "半期報告書",
	};
	const name = docTypeCodeToName[docTypeCode];
	return name;
};

// download xbrl
const resultRootFolder = "xbrl-files";
await Deno.mkdir(resultRootFolder, { recursive: true });
for (const [index, doc] of results.entries()) {
	const logPrefix = `[${index + 1}/${results.length}] `;

	const edinetCode = doc.edinetCode;
	const companyFolder = join(resultRootFolder, `${edinetCode}`);
	if (doc.docTypeCode === null) {
		console.warn(`${logPrefix}docTypeCode is null for ${doc.docID}`);
		continue;
	}
	const docType = docTypeCodeToName(doc.docTypeCode);
	if (docType === undefined) {
		console.warn(
			`${logPrefix}Unknown docTypeCode ${doc.docTypeCode} for ${doc.docID}`,
		);
		continue;
	}
	const submitDateTime = new Date(doc.submitDateTime)
		.toISOString()
		.split("T")[0];
	const docFolder = join(
		companyFolder,
		`${submitDateTime}_${doc.docID}_${docType}`,
	);

	console.info(`${logPrefix}Downloading ${doc.docID} to ${docFolder}`);

	await Deno.mkdir(docFolder, { recursive: true });

	const fileHandlingPromises: Promise<void>[] = [];
	fileHandlingPromises.push(
		Deno.writeTextFile(
			join(docFolder, "metadata.json"),
			JSON.stringify(doc, null, 2),
		),
	);

	if (doc.xbrlFlag === "1") {
		const xbrlFilePath = join(docFolder, `${doc.docID}_xbrl.zip`);
		fileHandlingPromises.push(downloadXBRL(doc.docID, xbrlFilePath));
	}

	if (doc.pdfFlag === "1") {
		const pdfFilePath = join(docFolder, `${doc.docID}.pdf`);
		fileHandlingPromises.push(downloadPDF(doc.docID, pdfFilePath));
	}

	if (doc.csvFlag === "1") {
		const csvFilePath = join(docFolder, `${doc.docID}_csv.zip`);
		fileHandlingPromises.push(downloadCSV(doc.docID, csvFilePath));
	}

	await Promise.all(fileHandlingPromises);
	// await new Promise((resolve) => setTimeout(resolve, 10));
}
