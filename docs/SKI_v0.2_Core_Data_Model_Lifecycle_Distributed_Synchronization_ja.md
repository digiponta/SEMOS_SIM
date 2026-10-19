# Semantic Knowledge Interchange (SKI) v0.2
## Core Data Model, Lifecycle & Distributed Synchronization
**公開技術仕様草案 / Independent Editor's Draft — 日本語版 — 2026-10-19**

> **Status:** 提案段階。W3C、ISO/IEC、JIS、Apache等による承認・推奨を意味しない。本ファイルはSKI v0.2 DOCX仕様書のリポジトリ内参照用Markdown版。正式語彙IRI・JSON-LD context・SHACL Shapesは未公開。

**目的:** Semantic Dataの共通表現（SDF相当）を **SKI-Core** に包含し、各VMが独立したSemantic Memoryを保持する環境において、知識の交換、評価、訂正、撤回、差分同期を相互運用可能にする。

## 仕様概要

| Profile | 責務 | 適合性 |
|---|---|---|
| SKI-Core | 命題、文脈、条件、出典、評価、識別子、版数 | Producer / Consumer |
| SKI-Lifecycle | 評価・承認・訂正・撤回・反映結果 | Lifecycle Processor |
| SKI-Sync | 差分同期、競合、再送、障害復旧 | Replica / Sync Peer |
| SKI-Internalization（任意） | 各VMの内部学習状態 | Internalization Reporter |
| SKI-Transport（任意） | TLS / RDMA等の転送アダプタ | Transport Adapter |

## 1. 範囲と原則

知識の受信、保存、承認、モデル内部への学習はそれぞれ独立した操作。SKIは知識の真実性を保証しない。実装や通信方式に依存せず、RDF、JSON-LD、PROV-O、SHACL、Nanopublicationsを再利用する。Apache Ossieのビジネス意味モデルとは競合せず、外部概念識別子を参照する。

**MUST/MUST NOT:** 適合必須。**SHOULD:** 逸脱理由の説明を要求する推奨。**MAY:** 任意。

## 2. SKI-Core: Canonical Semantic Data

| 必須度 | 属性 | 要件 |
|---|---|---|
| MUST | `assertionId` / `@id` | 安定したIRI/URN。異なるAssertionに再利用しない |
| MUST | `claim` | subject / predicate / object。IRIまたは型付きリテラルを優先 |
| MUST | `issuer` / `recordedAt` | 発行主体IRIとタイムゾーン付き時刻 |
| MUST | `version` | 1以上の整数。Assertion単位で単調増加 |
| MUST | `lifecycle` | CANDIDATE / APPROVED / SUPERSEDED / RETRACTED |
| SHOULD | `context` / `conditions` | 成立範囲、時間、例外 |
| SHOULD | `provenance` | PROV-Oによる来歴・根拠 |
| SHOULD | `assessments[]` | 評価主体・時刻・方法・状態 |
| MAY | `representations[]` | EmbeddingモデルID・次元・生成時刻・形式 |
| SHOULD | `accessPolicy` | 共有先・保護区分・ライセンス |

**規則:** Embedding、モデルパラメータ、ベンダー固有スコアによってClaimの同一性を決定してはならない。AssertionとAssessmentは分離し、矛盾する主体別評価を来歴付きで共存させる。

## 3. 状態の分離

| 種類 | 値 |
|---|---|
| Lifecycle | CANDIDATE / APPROVED / SUPERSEDED / RETRACTED |
| Epistemic | TRUE / FALSE / UNVERIFIED / CONTESTED / OUTDATED |
| Realization | EXTERNAL / CACHED / INTERNALIZED / UNKNOWN |

Assessmentは `assessor`、`assessedAt`、`method`、`status`、任意の0–1 `confidence`、`evidenceRefs` を含む。VM-Aでの承認はVM-Bの無条件承認を意味しない。INTERNALIZEDは再現能力やモデル重みからの完全除去を保証しない。

## 4. JSON-LD交換例

```json
{
  "@context": {
    "ski": "https://example.org/ski/v0.2#",
    "prov": "http://www.w3.org/ns/prov#"
  },
  "@id": "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
  "@type": "ski:KnowledgeAssertion",
  "ski:version": 2,
  "ski:issuer": {"@id": "https://example.org/vm/a"},
  "ski:recordedAt": "2026-10-19T09:00:00+09:00",
  "ski:lifecycle": "APPROVED",
  "ski:claim": {
    "ski:subject": {"@id": "https://example.org/concept/gpu"},
    "ski:predicate": {"@id": "https://example.org/rel/accelerates"},
    "ski:object": {"@id": "https://example.org/concept/matrix-work"}
  },
  "ski:conditions": [{"ski:description": "GPU最適化実装であること"}],
  "ski:assessments": [{
    "ski:assessor": "vm-a",
    "ski:status": "UNVERIFIED",
    "ski:assessedAt": "2026-10-19T09:00:00+09:00"
  }],
  "prov:wasDerivedFrom": {"@id": "https://example.org/evidence/001"}
}
```

**注意:** `example.org` は実際に公開されたSKI語彙を指さない。正式なJSON-LD context / SHACL shapesの公開は今後の作業。

## 5. SKI-Lifecycle

| 操作 | 内容 | 検証事項 |
|---|---|---|
| ASSERT | 新規主張の公開 | ID一意性、issuer、初期version |
| ASSESS | 来歴付きの評価追加 | assessor、evidence、時刻 |
| APPROVE | ローカル承認 | 承認権限・ポリシー |
| CORRECT | 後継レコードと置換関係 | previousVersion、eventId、来歴 |
| RETRACT | 撤回通知 | 権限、派生影響 |
| SYNC | 差分取得・適用確認 | 順序、欠落、重複、競合 |

MUST: RETRACTによって旧Assertionの監査履歴を隠してはならない。CORRECTは後継との関係を保持する。MUST NOT: 受信側は外部APPROVEを無条件承認と扱わない。

## 6. SKI-Sync: VM間分散Semantic Memory

VM-A、VM-B、VM-Cは各自の独立Semantic Memory、Local Assessment、Internalization Stateを持つ。共有Assertion・イベント集合の収束を目指すが、各VMの評価やモデルパラメータの一致は要求しない。

同期イベント要素:
- `eventId`: 冪等性用ID
- `assertionId`: 対象レコード
- `issuer` / `originVm`: 認証済み発行者・起点
- `previousVersion` / `newVersion`: 版数の前提と結果
- `timestamp`: 監査時刻（唯一の順序根拠にはしない）
- `operation` / `payloadDigest`: 操作と検証用ダイジェスト
- `causalParents[]`: 任意の因果参照
- `applyStatus`: RECEIVED / VALIDATED / COMMITTED / REJECTED / CONFLICT

受信処理の順序は「認証 → 構造検証 → 版数照合 → ローカルトランザクション → 受領応答」。再送はeventIdによって重複適用を防止する。欠落版は保留して差分またはスナップショットを要求する。因果的に独立した同時訂正はLast-Writer-Winsだけで解決せず、競合と来歴を保全する。

## 7. SKI-Internalization (/sleep)

モデル学習はローカル操作であり、同期適用の完了とは別の状態を持つ。実装時には `vmId`、`modelId`、`checkpointId`、版数付き`inputAssertionIds`、`startedAt`、`completedAt`、`trainingStatus`、`validationResult` を記録する。

撤回を受信しても学習済み重みからの完全削除を保証してはならない。必要に応じて検索側の遮断、再学習、モデル切替、再評価を行う。

## 8. SKI-Transport と RDMA

SKIはトランスポートに依存しない。小規模イベント・認証・受領応答にはTCP/TLSを利用できる。大容量Embeddingバッチ、添付知識、スナップショットには任意のRDMAアダプタを使用できる。

**RDMA Write完了 ≠ SKI COMMITTED。** 受信側が権限・ダイジェスト・版数を確認しローカルCommitした時点でのみCOMMITTEDとなる。RDMAを利用できない環境でも同じSKI意味論をTCP/TLSで提供する。

## 9. セキュリティ・プライバシー

- MUST: 主張とイベントの発行者を認証し、権限外の操作を拒否する。
- MUST: 外部根拠文書の内容を命令として実行しない（プロンプトインジェクション防止）。
- SHOULD: JSON-LD外部コンテキスト・URIのリモート取得を制限し、SSRF・過大入力を防止。
- SHOULD: 個人情報・機密性・ライセンス・保持期限・監査方針を定義。
- MUST NOT: 同期成功を真偽保証、内部学習成功、永続化完了と混同しない。

## 10. 適合性と試験計画

| 実装クラス | 最低限の試験 |
|---|---|
| Core Producer | 必須属性、Claim構造、版数、JSON-LD |
| Core Consumer | 構造検証、未知語彙方針、来歴保持 |
| Lifecycle Processor | APPROVE/CORRECT/RETRACTの履歴・認可 |
| Sync Peer | 冪等性、順不同、欠落、競合、障害復旧 |
| Internalization Reporter | Assertion版数とcheckpointの対応 |
| Transport Adapter | TCP/RDMAで論理結果一致、ダイジェスト検証 |

推奨PoCは**3VM×各100知識レコード**。同時訂正、部分障害、再接続、競合Assessment、撤回、/sleep前後を試し、収束率・P50/P95同期遅延・転送量・競合検出率・誤反映率・内部化追跡率を測る。**現時点で適合性テストが完了したとは主張しない。**

## 11. 既存標準との差異と新規性の境界

RDF/JSON-LDは意味構造、PROV-Oは来歴、SHACLは検証、Nanopublicationsは主張単位、VCは発行者検証、Apache Ossieはビジネス意味モデル、MCP/A2Aは連携・通信を提供する。SKIの焦点は**AI管理知識の評価・訂正・撤回・モデル内部化状態を異種Semantic Memory間で伝えるライフサイクル・プロファイル**である。正式な既存標準マッピングと独立評価は今後の課題。

## 12. 公開・ガバナンス

v0.2は独立技術仕様草案。正式な語彙IRI、JSON-LD Context、SHACL Shape、参照実装、ライセンス・変更管理手続きは未完成。v0.3で語彙とValidator、v0.4で3VM同期・撤回伝播、v0.5で第三者Consumer適合性試験を優先する。

## 参考資料

- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/)
- [RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/)
- [PROV-O](https://www.w3.org/TR/prov-o/)
- [SHACL](https://www.w3.org/TR/shacl/)
- [Verifiable Credentials Data Model v2.0](https://www.w3.org/TR/vc-data-model/)
- [Nanopublications](https://nanopub.net/)
- [Apache Ossie](https://ossie.apache.org/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
