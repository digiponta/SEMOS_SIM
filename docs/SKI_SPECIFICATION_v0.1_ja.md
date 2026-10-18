# Semantic Knowledge Interchange Specification v0.1

**SKI — Semantic Data / Semantic Memory 相互運用仕様**  
**公開技術仕様草案 / Editor's Draft — 2026-10-18**  
**Status:** 独立提案仕様。W3C・ISO・JIS等が承認した標準ではない。

> 本文の正式な文書版は `Semantic_Knowledge_Interchange_Specification_v0.1_ja.docx`。このMarkdownはリポジトリに登録する実装者向け公開ドラフトであり、仕様化に必要な規範要素をまとめたものである。

## 1. 目的と範囲

異なるLLM、AIエージェント、Semantic OS、Semantic Memory、知識グラフ、分散知識サービス間で、知識の主張・条件・文脈・来歴・評価状態・アクセス条件・変更履歴を交換する。LLMのモデル重み移転、科学的真理の自動判定、重みからの完全削除保証、異なるEmbedding間の意味同値証明は範囲外とする。

**MUST / MUST NOT**は適合性の必須要件、**SHOULD**は理由を明記した逸脱が可能な推奨、**MAY**は任意とする。

## 2. 設計原則

- モデル非依存：Canonical Claimの同一性はEmbeddingやLLMパラメータから独立。
- 主張と評価の分離：TRUE/FALSE等は評価主体・時刻・根拠を伴うAssessmentで表す。
- 出典・来歴：PROV-Oを利用し、根拠への参照そのものを真実性保証とみなさない。
- 追跡可能な履歴：訂正・撤回は上書きで隠さず、イベントとして保持。
- 受信側の裁量：受領しても自動承認・自動内部学習・権限付与しない。
- データ最小化：個人・機密・著作権・保持期間等のポリシーを尊重。

## 3. 用語

| 用語 | 意味 |
|---|---|
| Assertion | 主張を記録した単位。ID、Claim、状態、発行主体、版数を持つ |
| Claim | subject / predicate / object と任意qualifierの命題 |
| Context | 時間・場所・分野・適用環境など意味の限定 |
| Evidence | 根拠参照。参照があるだけで真実とは限らない |
| Assessment | 誰が・いつ・どの方法で下した評価 |
| Event | 主張の追加・評価・訂正・撤回を伝える更新通知 |
| Recipient | 交換された知識を受け取るシステム |

## 4. SKI-Coreのデータ要素

| フィールド | 型 | 要件 |
|---|---|---|
| `@id` | IRI | MUST: 安定したAssertion識別子 |
| `@type` | IRI | MUST: `ski:KnowledgeAssertion` |
| `ski:claim` | Object | MUST: 構造化されたsubject/predicate/object |
| `ski:recordedAt` | dateTime | MUST: タイムゾーン付き |
| `ski:issuer` | IRI | MUST: 発行主体 |
| `ski:lifecycle` | enum | MUST: 管理状態 |
| `ski:version` | integer | MUST: 1以上、更新に伴って単調増加 |
| `ski:assessments` | Array | SHOULD: 評価主体別の判断 |
| `prov:wasDerivedFrom` | IRI[] | SHOULD: 出典・根拠 |
| `ski:accessPolicy` | IRI | SHOULD: 共有制約 |
| `ski:conditions` | Object[] | MAY: 成立条件 |
| `ski:context` | Object[] | MAY: 文脈 |

Assertion ID（例：HTTPS IRI、urn:uuid）は再利用しない。同じ命題でも発行主体が違えば独立したAssertionとして保存してよい。IRI・言語タグ・型付きリテラルの正規化方針を明示し、テキスト類似度だけで同一性を決定してはならない。

## 5. 別々に保持すべき状態

| 区分 | v0.1語彙 |
|---|---|
| Lifecycle | `CANDIDATE` / `APPROVED` / `SUPERSEDED` / `RETRACTED` |
| Epistemic Assessment | `TRUE` / `FALSE` / `UNVERIFIED` / `CONTESTED` / `OUTDATED` |
| Memory realization | `EXTERNAL` / `CACHED` / `INTERNALIZED` / `UNKNOWN` |

Assessmentは `assessor`、`assessedAt`、`method`、任意の`confidence`（0～1）、根拠参照を保持する。内部化（INTERNALIZED）はモデルが知識を再現できることや、撤回時に完全に削除できることを保証しない。

## 6. JSON-LD交換例

```json
{
  "@context": {
    "ski": "https://example.org/ski/v0.1#",
    "prov": "http://www.w3.org/ns/prov#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "issuer": {"@id": "ski:issuer", "@type": "@id"},
    "recordedAt": {"@id": "ski:recordedAt", "@type": "xsd:dateTime"}
  },
  "@id": "urn:uuid:2ff02d96-7377-4e65-9108-7c1593f6b90a",
  "@type": "ski:KnowledgeAssertion",
  "issuer": "https://example.org/agents/producer-A",
  "recordedAt": "2026-10-18T10:00:00+09:00",
  "ski:version": 1,
  "ski:lifecycle": "CANDIDATE",
  "ski:claim": {
    "@type": "ski:StructuredClaim",
    "ski:subject": {"@id": "https://example.org/concepts/gpu"},
    "ski:predicate": {"@id": "https://example.org/relations/accelerates"},
    "ski:object": {"@id": "https://example.org/concepts/matrix-computation"}
  },
  "ski:conditions": [
    {"@type": "ski:Condition", "ski:description": "適切なGPU実装を利用する場合", "ski:language": "ja"}
  ],
  "ski:assessments": [
    {
      "@type": "ski:Assessment",
      "ski:epistemicStatus": "UNVERIFIED",
      "ski:assessor": {"@id": "https://example.org/agents/producer-A"},
      "ski:assessedAt": "2026-10-18T10:00:00+09:00"
    }
  ],
  "prov:wasDerivedFrom": {"@id": "https://example.org/evidence/benchmark-1"}
}
```

`https://example.org/ski/v0.1#`は例示用であり正式な公開・解決可能URIではない。`application/ld+json`を推奨する。未承認の外部JSON-LDコンテキストを自動取得してはならない（SSRF等の対策）。

## 7. SKI-Exchangeイベントプロファイル

SKI-CoreではオフラインJSON-LD交換を最低限の相互運用単位とする。任意のSKI-Exchangeプロファイルでは、`ASSERT`、`ASSESS`、`CORRECT`、`RETRACT`を定める。各イベントは`eventId`、`assertionId`、`previousVersion`、`newVersion`、`issuer`、`timestamp`、`operation`および変更データを含む。

- 重複eventId：冪等処理で二重反映しない。
- バージョン欠落：追加イベント要求、または保留。
- 競合修正：両方の来歴を保全して受信側ポリシーで解決。
- 撤回：外部記憶で無効化し派生データへ通知。ただしLLM重みからの削除は保証しない。
- 同期相手の本人確認・署名または同等の認証・受領応答を推奨する。

## 8. セキュリティとプライバシー

受領前のスキーマ検証、権限検査、出所認証を行う。根拠文書や知識内容を命令として実行してはならず、プロンプトインジェクションに備える。遠隔URI取得やリダイレクトを制限する。暗号技術は独自設計せず既存の成熟した標準を利用する。ライセンス、秘密情報、個人情報、保有期限、越境移転を別の実装ポリシーで制御する。

## 9. 適合性要件

- **SKI-Core Producer:** 必須情報、安定ID、version、発行主体、時刻、構造化Claimを持つJSON-LD生成。
- **SKI-Core Consumer:** 必須情報検証、未知語彙の勝手な改変禁止、評価と来歴の保持、不正データの拒否・隔離。
- **SKI-Exchange Peer:** eventId冪等性、順序検査、撤回伝播、競合保全、受領応答。

検証には不完全な主張、IRI衝突、未解決コンテキスト、複数Assessment、重複イベント、欠落イベント、同時修正、撤回、権限外URI、別Embeddingモデルを含める。**機械可読語彙・SHACL Shape・公式適合性テストはv0.1時点では未完成**。

## 10. 今後の計画

| 版 | 成果物 |
|---|---|
| v0.1 | 技術仕様草案、JSON-LD交換例、Core/Exchange要件案 |
| v0.2 | 正式語彙IRI、SHACL Shape、検証器、サンプル |
| v0.3 | Python参照実装、LLM_SEM→LLM_TRY往復試験 |
| v0.4 | 分散同期・競合解決・撤回伝播テスト |
| v0.5 | 第三者独立実装との互換試験とセキュリティレビュー |
| v1.0候補 | 公開レビュー・変更管理・互換性・ガバナンス確立 |

推奨PoC：LLM_SEMから100件をSKI形式で書き出し、LLM_TRYと独立Consumerに取り込んで主張・条件・来歴・評価・履歴の保持を検証。訂正・撤回・重複配信・矛盾する評価の併存を確認する。

## 11. 既存標準

- JSON-LD 1.1: https://www.w3.org/TR/json-ld11/
- RDF 1.1 Concepts: https://www.w3.org/TR/rdf11-concepts/
- PROV-O: https://www.w3.org/TR/prov-o/
- SHACL: https://www.w3.org/TR/shacl/
- DCAT 3: https://www.w3.org/TR/vocab-dcat-3/
- ODRL: https://www.w3.org/TR/odrl-model/
- MCP: https://modelcontextprotocol.io/specification/

本提案は標準化団体の公式な承認や提携を意味しない。正式公開に向け、語彙URI、ライセンス、発行主体、変更管理プロセスを別途定める。
