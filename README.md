# XBRL-Extractor

Edinet の XBRL をダウンロードして、パースして、財務諸表を抽出するツール。

# 使い方

## XBRL のダウンロード

```
deno --allow-net --allow-write --env-file .env download_xbrl_from_edinet.ts
```

`DATE_RANGE` で期間を調整。 API キーやエンドポイントを .env に記述。

## XBRL のパース

```
python extract_financial_statements_from_xbrl_v2.py
```

JSON で出力される。

## 集約してフロントエンドの一覧ページ用の JSON を生成

```
python aggregate_company_metadata.py
```
