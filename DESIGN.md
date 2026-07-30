# 出欠管理システム デザイン言語

Web 管理コンソール（Flask + Jinja）と Flutter アプリが**共通で参照する唯一の基準**。
プラットフォームで実装が分かれる箇所は `Web:` / `Flutter:` で書き分ける。

- 確定日: 2026-07-30
- 利用者: ZENSHIN robotics の中高生部員と執行役。**非専門家・スマホ主体・日本語**
- 優先順位: **「迷わず出欠を出せる」> 見た目**

## 根拠の扱い

数値には出典を併記する。出典の強さは混ぜない（`latest-ui-ux-insights.md` 冒頭の分類に従う）。

| 記号 | 意味 |
|---|---|
| **[W3C]** | WCAG 達成基準・CSS 仕様。適合義務がある |
| **[機械可読]** | `api.webstatus.dev` / MDN BCD。事実として確定 |
| **[ベンダー]** | web.dev / Apple / Google / Flutter。所有者だが規範ではない |
| **[1社DS]** | Carbon / PatternFly / Cloudscape / Astro。業界標準ではない |
| **[公的機関]** | デジタル庁デザインシステム（DADS）。日本語UIの一次ソース |
| **[実測]** | 参照文書内で測定されたもの |
| **[本書算出]** | 本書で計算・検証したもの。参照文書には無い |
| **未回答** | 一次ソースが無い。**推測で埋めない** |

参照文書（`C:\Users\kayah\.claude\docs\`）:
`web-design-2026.md` = **[W]**、`latest-ui-ux-insights.md` = **[L]**、`flutter-app-ui-2026.md` = **[F]**

> **各文書の「否決された主張」章は引用しない。「未回答」章を推測で埋めない。**

---

## 1. カラートークン

### 1.1 記法は OKLCH

**[1社DS]** Tailwind v4 / shadcn の既定トークンはすべて `oklch()`（[W] §3.1）。
明度をライト/ダークで反転させる用途に適している。

> スコープ: これは既定トークンと慣習であって技術的制約ではない（[W] §3.1 の注記そのまま）。

### 1.2 ダークの面は純黒でなく暗いグレー

**[ベンダー]** 根拠は **Material 2 のみ**。Apple HIG には該当記述が無いことを DocC JSON 全文検索で確認済み、
Material 3 と IBM Carbon は一次ソース自体が存在しない — これは「未調査」ではなく**確定した否定結果**（[L] §3.3 / §6）。

> "A dark theme uses **dark grey, rather than black**, as the primary surface color... it's easier to see shadows on grey (instead of black)... **reduce eye strain**"
> "The recommended dark theme surface color is **`#121212`**... If a dark color is preferred instead, ensure that it passes the **15.8:1 contrast ratio**."

**「純黒禁止」と書かない。** Material 2 自身が `#121212` を "a recommendation" と位置づけ、
**OLED のバッテリー節約目的での純黒使用を許容している**（[L] §3.3）。

**[本書算出]** 採用する暗色が Material 2 の 15.8:1 基準を満たすことを計算で確認した:

| 面 | OKLCH | HEX | 白に対して |
|---|---|---|---|
| ダーク背景 | `oklch(0.190 0.004 265)` | `#131416` | **18.43:1** ✅ |
| （参考）M2 推奨 | — | `#121212` | 18.73:1 |

### 1.3 面のトークン

ソリッドな面のみで階層を作る。**グラデーションとガラスは使わない**（§6）。

```
--bg               ページ背景
--surface          カード・パネルの面
--surface-2        その上に乗る面（入力欄・テーブルヘッダ）
--border           境界線（装飾）
--border-strong    入力欄など操作対象を示す境界線
--fg               本文
--fg-muted         補助テキスト
--accent           主要操作
--ring             フォーカスリング
--highlight-flash  「この行が更新された/移動先はここ」の一時的な強調
```

**境界線を2種類に分ける理由**: **[W3C]** SC 1.4.11 Non-text Contrast（AA）が 3:1 を要求するのは
**情報を伝える**非テキストで、純粋な装飾の罫線は対象外。
カード枠や表の罫線は装飾なので `--border`（1.35:1）でよいが、
**入力欄の枠は「どこが入力欄か」を伝える唯一の手がかり**なので 3:1 を満たす必要がある。
1本のトークンで兼ねると、罫線だらけになるか基準を割るかのどちらかになる。

**`--highlight-flash` を独立させる理由**: ステータス色は §2 で状態表現に予約されている。
「行が更新された」という**状態と無関係な演出**にステータス色（例: 部分参加のチップ色）を流用すると
色の意味が混ざり、§2.2 の「強い色は要対応に予約し pop-out を無駄遣いしない」に反する。
ステータス4色と**色相が明確に異なる中立寄りの淡色**を1つ用意する。

**[本書算出]** 確定値（sRGB 変換後に検証。全て色域内）:

| トークン | ライト | ダーク |
|---|---|---|
| `--bg` | `oklch(1 0 0)` `#FFFFFF` | `oklch(0.190 0.004 265)` `#131416` |
| `--surface` | `#FFFFFF` | `oklch(0.240 0.005 265)` `#1E1F22` |
| `--surface-2` | `oklch(0.975 0.003 265)` `#F6F7F9` | `oklch(0.290 0.006 265)` `#2A2B2E` |
| `--border` | `oklch(0.900 0.005 265)` `#DCDEE1` | `oklch(0.370 0.008 265)` `#3E4044` |
| `--border-strong` | `#8D8F93`（白背景に **3.24:1**） | `#6D6F72`（ダーク背景に **3.66:1**） |
| `--fg` | `oklch(0.270 0.008 265)` `#24262A` | `oklch(0.930 0.004 265)` `#E6E8EB` |
| `--fg-muted` | `oklch(0.530 0.010 265)` `#696C72` | `oklch(0.720 0.008 265)` `#A2A5AA` |
| `--ring` | `oklch(0.550 0.150 255)` `#2971C6` | `oklch(0.700 0.130 255)` `#64A1EE` |
| `--highlight-flash` | `oklch(0.930 0.030 245)` `#D8EBFB` | `oklch(0.330 0.040 245)` `#233849` |

検証結果（ライト / ダーク）: 本文 15.15 / 15.01、補助テキスト 5.26 / 7.46、
フォーカスリング 4.92 / 6.91（**SC 1.4.11 の 3:1 を満たす**）、
**点滅中の本文 12.41 / 9.87**（ハイライトが被っても本文が AA を割らない）。

`Web:` ライト/ダークの切替は **`color-scheme` + カスタムプロパティの差し替え**で行う。

**[機械可読]** `color-scheme` は **Baseline Widely**（2022-01 から利用可）。
一方 `light-dark()` は **Baseline Newly（2024-05）で、Widely 到達は最速 2026-11**（[L] §3.1、取得日 2026-07-29）。
**現時点では `light-dark()` 単独に依存しない。** 使うなら progressive enhancement に留める。

**[ベンダー]** `light-dark()` を使う場合 `color-scheme: light dark` の宣言が必須。
無いと機能しないのは**ドキュメント化された失敗モード**（[L] §3.3）。

```css
:root {
  color-scheme: light dark;   /* Widely。UA の canvas/スクロールバー/フォーム既定色に効く */
  --bg: #FFFFFF; --surface: #FFFFFF; --border: oklch(0.90 0.004 265);
}
@media (prefers-color-scheme: dark) { :root { --bg: oklch(0.190 0.004 265); /* … */ } }
:root[data-bs-theme="dark"]  { /* 手動オーバーライドは属性で上書き（既存実装を踏襲） */ }
:root[data-bs-theme="light"] { /* 逆方向も明示的に勝たせる */ }
```

**[ベンダー]** 手動オーバーライドを永続化する場合、FOUC 回避には
**`<head>` 内・全 CSS より前のブロッキング `<script>`** が機構上必須（[L] §3.3）。
`<link rel="stylesheet">` の後に置くと取得でブロックされ手法が破綻する。
**システム追従だけなら JS は不要。**

`Flutter:` `ThemeData` は **light/dark それぞれコンストラクタで一発生成する**。
**[ベンダー]** `copyWith` で `useMaterial3: true` にしても既存プロパティは M3 既定に更新されない、と
API doc が明記している（[F] §1.4）。継ぎ足すと **M3 が半分しか効かない状態**になる。

---

## 2. ステータス色

### 2.1 status と severity は別の軸にする

**[1社DS]** PatternFly は status（対象の現在状態）と severity（問題の深刻度）を別物として定義し、
トークン名前空間もアイコンセットも分けている（[W] §1.1）。

> "Status does not automatically convey the level of impact an issue may have."

> スコープ注意: **これは PatternFly 1社の規定であって業界コンセンサスの証拠ではない**（[W] §1.1 の注記そのまま）。

本システムへの適用:

| 軸 | 値 | 意味 |
|---|---|---|
| **status** | 出席 / 部分参加 / 欠席 / 未回答 | 出欠の状態。**4値。ドメインが決めている** |
| **severity** | 要対応 / それ以外 | **2値のみ。** 「自分がまだ出欠を出していない」＝要対応 |

**severity を2値に絞る根拠**: [W] §1.2 が Astro の6段階について
「一般利用者が10件程度を見る画面では **実際に行動が変わるのは3〜4段階**」とし、
[W] §6 が「Astro の6段階と PatternFly の2軸6値は、一般利用者には段階が多すぎる可能性が高い」と明記している。
部員が取る行動は「出欠を出す」の1つなので **2値で足りる**。

### 2.2 欠席は異常ではない — 強調は「未回答」に予約する

**[1社DS] + [コンサル]** [W] §1.4 の結論をそのまま適用する。

> **要対応だけに強い色とアイコンを与え、正常は視覚的に静かに保つ**
> 「Stephen Few の pre-attentive 論のとおり、逐次走査より色/形の pop-out が速いが、**全部を装飾すると pop-out は消滅する**」

現在の実装は **欠席を赤で塗っている**（`status_chip.dart:14` `Colors.red`）。
欠席は正当な回答であって異常ではないため、赤の警告的な扱いは pop-out を無駄に消費する。

**方針**: 出席・部分参加・欠席は**同格の「回答済み」として静かに**扱う。
**強い視覚的重みは `未回答`（＝要対応）にだけ与える。**

### 2.3 コントラスト — Carbon の3条件は4状態では原理的に成立しない【本書算出】

**[1社DS]** Carbon（2026-07-28 更新）の規定（[W] §2.2）:

> "ensure that there's at least a **3:1 contrast between colors used for status indicators**, as well as **between the indicator and the page background**. If the contrast is sufficient, even in grayscale, users should still be able to differentiate statuses without relying solely on color."

[W] §2.2 はこれを3つのテストに落としている:
① ステータス色同士が 3:1 以上 ② ステータス色と背景が 3:1 以上 ③ グレースケールでも区別できる

**[本書算出] ① と ② は3色以上で同時に満たせない。** WCAG のコントラスト比は相対輝度 Y のみの関数
`(Yhi+0.05)/(Ylo+0.05)` なので、算術で決まる:

```
白背景(Y=1.0)と 3:1 を満たす → Y ≤ 1.05/3 − 0.05 = 0.3000
そこから 3:1 刻みで下に積む  → 0.3000 → 0.0667 → −0.0111（負）
∴ 白背景で「全ペア3:1」かつ「背景と3:1」を満たせるのは最大 2 色
```

出欠は4状態なので**原理的に不可能**。実際に4色を一律 4.5:1 で解くと
**ペア間コントラストは 1.00〜1.03:1**（＝グレースケールで完全に区別不能）になることも計算で確認した。

さらに sRGB の色域制約が重なる。**黄系（部分参加）は暗くすると色域外に出る**ため、
`h=70 / C=0.12` では白チップ上の 4.5:1 に到達できず、`h=60 / C=0.10` まで落とす必要があった。

**したがって本システムの規約はこうする:**

| 項目 | 規約 | 根拠 |
|---|---|---|
| テキストとしての前景色 | **チップ背景・ページ背景の両方に対し 4.5:1 以上** | **[W3C]** SC 1.4.3 Level AA |
| アイコン・境界線 | 3:1 以上（上記を満たせば自動的に達成） | **[W3C]** SC 1.4.11 Level AA |
| ペア間 3:1 / グレースケール区別 | **達成不能。放棄する** | **[本書算出]**（上記の証明） |
| 代替として必須 | **アイコン形状 + テキストラベルを常に併記** | **[W3C]** SC 1.4.1 Level A |

**②を放棄しても法的要件は満たす。** 色を唯一の伝達手段にすることを禁じているのは SC 1.4.1（Level A）で、
**テキストがあれば 1.4.1 は満たせる**（[W] §2.1 の逐語）。①③は Carbon 1社の推奨であって W3C 要件ではない。

**[コンサル]** アイコンは法的要件ではないが知覚速度の最適化として強く推奨する。
NN/g の調査で「アイコン+色」がテキストのみより **37%高速**（[W] §2.1）。
**[1社DS]** ただし PatternFly は無色のアイコン使用を禁止しているので、**色を捨てて形だけにするのも不可**（[W] §2.1）。

### 2.4 確定した値【本書算出・検証済み】

`oklch()` で著者定義し、sRGB 変換後に WCAG コントラスト比を計算して検証した。**全て色域内。**

**ライト（ページ背景 `#FFFFFF`）**

| status | 前景 OKLCH | 前景 | チップ背景 | 前景/チップ | 前景/ページ |
|---|---|---|---|---|---|
| 出席 | `oklch(0.528 0.13 150)` | `#207F40` | `#E9F6EB` | **4.52:1** | 5.03:1 |
| 部分参加 | `oklch(0.547 0.10 60)` | `#9B612E` | `#FEEFE3` | **4.51:1** | 5.07:1 |
| 欠席 | `oklch(0.552 0.15 25)` | `#BA4643` | `#FDECEA` | **4.54:1** | 5.19:1 |
| 未回答 | `oklch(0.539 0.02 265)` | `#696E7A` | `#F0F2F4` | **4.55:1** | 5.11:1 |

**ダーク（ページ背景 `#131416`）**

| status | 前景 OKLCH | 前景 | チップ背景 | 前景/チップ | 前景/ページ |
|---|---|---|---|---|---|
| 出席 | `oklch(0.617 0.13 150)` | `#419B5A` | `#18271B` | **4.51:1** | 5.32:1 |
| 部分参加 | `oklch(0.636 0.12 70)` | `#B97C2B` | `#2D2011` | **4.51:1** | 5.25:1 |
| 欠席 | `oklch(0.646 0.15 25)` | `#DA645E` | `#331C1A` | **4.51:1** | 5.24:1 |
| 未回答 | `oklch(0.631 0.02 265)` | `#838A96` | `#212326` | **4.53:1** | 5.30:1 |

**アイコンは形状で区別する**（色を落としても意味が残るように）:

| status | 形 | Web (bootstrap-icons) | Flutter (Material) |
|---|---|---|---|
| 出席 | チェック | `bi-check-circle-fill` | `Icons.check_circle` |
| 部分参加 | 半分 | `bi-circle-half` | `Icons.timelapse` |
| 欠席 | 横線 | `bi-dash-circle-fill` | `Icons.remove_circle` |
| 未回答 | 疑問 | `bi-question-circle` | `Icons.help_outline` |

> 現行実装の欠席は `Icons.cancel`（✕）。✕ は「エラー・失敗」の含意が強いため、
> §2.2 の方針（欠席は異常ではない）に合わせて**横線**に変える。

**Astro UXDS の色は使わない。** ライトの塗り値 `#FCE83A` `#56F000` `#FAD800` `#00E200` は
**白背景のテキスト色として AA を満たさない**と Astro 自身が明記しており、用途を
「ボーダー付きステータスシンボルの塗り」に限定している（[W] §2.4）。
加えて Astro は**保守終了**、Standby のライト塗りは HEX と RGB が矛盾している（[W] §2.4 / §6）。

### 2.5 集約と一覧

**[1社DS]** 複数の status をまとめて1つ出すときは**最も重いもの**を採る。
Astro と IBM Carbon が独立にほぼ同一の文言で規定している（[W] §1.2）。

```
未回答 > 欠席 > 部分参加 > 出席
```

**[1社DS]** サマリー帯は**重い順**に並べ、**各アイコンに件数を付ける**（PatternFly、必須規定。[W] §1.3）。
件数から絞り込めるようにするのは任意。

```
要対応 3 ／ 欠席 2 ／ 部分 1 ／ 出席 12
```

**[1社DS] + [コンサル]** カードで全カードの要素配置を完全に固定し、severity 降順を既定ソートにする（[W] §1.4）。

> **「何件以上ならテーブル」という定量閾値は否決済み**（[W] §4-a）。**件数で機械的に決めない。**

---

## 3. タイポグラフィ

### 3.1 サイズの下限は 14px

**[公的機関]** DADS の逐語（[L] §4.1）:

> "**14 CSS px未満の大きさの使用は原則として許容されません。**"

サイズ帯: 48–64px（視覚的インパクト）/ **16–45px（見出し・本文）** / 14px（制約がある場合のみ、例: フッター）。

`Web:` **現行 `style.css:4` の `--bs-body-font-size: 0.875rem`（14px）は是正する。**
14px は DADS の「制約がある場合のみ」に該当し、本文の既定値としては帯から外れている。
**本文は 16px（`1rem`）に戻す。** テーブル等の高密度領域だけ 14px を許容する。

> 併記すべき事実: **[1社DS]** Carbon の data-table は Column header / Row text を **14px** で運用している
> （出荷 CSS でも確認済み。[L] §2.4）。つまり「テーブル内 14px」は 1社DS の実例として支持がある。
> ただし DADS の帯とは緊張関係にあるので、**本文には広げない。**

### 3.2 行高

**[公的機関]** DADS（[L] §4.1）:

> "読み物コンテンツにおける本文テキストの行ボックスの高さ（行高）はフォントサイズに対して**少なくとも1.5倍**を維持することを推奨します。"

離散スケールが公開されている:

| 行高 | 用途 |
|---|---|
| 100% | ボタン等の1行コンポーネント |
| **120% / 130%** | **管理画面・業務システム（情報密度優先）** |
| 140% | 見出しなど大きな文字 |
| **150%** | 一般的なWebの本文（**最低値**） |
| 160% | 一般的なWebの本文 |
| 170% / 175% | 心理的負荷を下げたい本文 |

採用値:

| 用途 | 行高 |
|---|---|
| 本文（ダッシュボード・説明文） | **1.6** |
| テーブル行・チップ | **1.3**（DADS の管理画面帯） |
| ボタン・1行ラベル | **1.0** |
| 見出し | **1.4** |

> **未回答**: 「では 150% と 160% のどちらが良いか」の根拠は**存在しない**。
> [W] §5-4 で「英語圏設計システムのスケールを日本語にそのまま当てたときの可読性は誰も検証していない」とされ、
> [F] §9-4 でも「M3 は和文に行間を足していないことは分かったが、**ではいくつが良いのかの根拠は無い**」と再確認されている。
> **上記はDADSの離散スケールから選んだ値であって、最適値の主張ではない。**

**[公的機関]** 段落間隔は**行ボックス高の1.5倍以上（＝フォントサイズの2.25倍以上）**（[L] §4.1）。

**[W3C]** 行長は**全角40文字**程度。これは DADS 独自ではなく
**WCAG 2.2 SC 1.4.8 視覚的提示（Level AAA）に帰属**すると DADS 自身が明記している（[L] §4.1）。
AAA なので必須ではないが、読み物領域では守る。

### 3.3 フォントスタック

**[公的機関]** DADS の本文用 `font-family` は3回の独立取得で一致した、**たった4トークン**（[L] §4.1）:

```css
font-family: 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
```

> **`Hiragino Sans` / `Yu Gothic` / `游ゴシック` / `メイリオ` はページ内のどこにも出現しない。**
> 「日本語UIは Hiragino → Yu Gothic → Noto Sans JP の順で指定する」という広く見る書き方は **DADS の規定ではない**（[L] §4.1）。

`Web:` **現行 `style.css:3` の `'Noto Sans JP', 'Helvetica Neue', Arial, sans-serif` を DADS の4トークンに合わせる。**
`Helvetica Neue` / `Arial` は和文グリフを持たないため実質フォールバックとして機能しておらず、
`-apple-system` / `BlinkMacSystemFont` を置く方が iOS/Android の実機で意図した結果になる。

> DADS 自身が "なおこれは、OSやデバイスネイティブのシステムフォントの使用を制限するものではありません。" と明記（[L] §4.1）。

### 3.4 Flutter の行箱は Web と別物として扱う

**ここは両プラットフォームで数値を共有できない。** [F] 第5部の実測（Flutter 3.41.9）:

**[実測]** 同じ `fontSize: 16` でフォントにより**行箱が 44% 変わる**（[F] §5.1）:

| フォント | 自然行高 | fontSize 16 の行箱 |
|---|---|---|
| Noto Sans JP (2.004-H2) | **1.448em** | **23.0px** |
| BIZ UDPGothic (1.051) | **1.000em** | **16.0px** |

**[実測]** **M3 の `height: 1.43` は Noto Sans JP の自然行高 1.448em より小さいので、和文では行間を足していない**（[F] §5.4）。
M3 の dense（CJK用）と englishLike の違いは `textBaseline` が `ideographic` であることだけで、**数値は完全に同一**。
→ **日本語本文の行間は自分で指定する。**

**[ベンダー] + [実測]** `leadingDistribution` の既定は `proportional` で、Noto Sans JP では
**1160:288 ≒ 80:20 で配られ和文が下に沈む**。`even`（CSS のハーフレディング相当）にする。
**M3 の `TextTheme` は既に全スタイルに `even` を入れている**ので、`Theme` 経由なら既定で直っている（[F] §5.2）。

**[実測]** 段落の上下だけ余白を削るには `textHeightBehavior`。
NSJP fontSize 16 / height 1.75 で **1行 32.0px → 23.0px、3行 84.0px → 80.0px（行送り 28.0px は維持）**（[F] §5.3）。
カード内テキストの詰めに使う。

**[実測]** `palt` は約物が多い文で **−16〜−22%** 詰まる（[F] §5.6）。
OpenType 仕様自身が "**UI suggestion: This feature should be off by default.**" と書いているので、
**見出し限定**にする。本文全面適用はしない。`BIZ UDPGothic には palt が無い`。

**[実測]** `letterSpacing` の罠2つ（[F] §5.5）:
1. **最後の1文字の後ろにも加算される**
2. **`textScaler` でスケールされない** → 文字サイズを上げると相対的に字間が詰まって見える

**[実測]** 和欧混在で行の高さが変わる（"Hello world" 19.0px vs 日本語を含む行 23.0px、**21%差**）。
`StrutStyle` の `forceStrutHeight` で揃えられるが、公式 doc が
"**text in adjacent lines may overlap**" / "**bypasses a large portion of the vertical layout system**" と警告しているので、
**行が必ず揃わなければ困る箇所に限定する**（[F] §5.8）。

**[ベンダー]** フォントスケール追従は `TextScaler`。`textScaleFactor` は非推奨。
**Android 14 以降のフォントスケールは最大200%かつ非線形**で、
Flutter 側も "**textScaleFactor should not be used in arithmetic operations**" と明記している。
**掛け算に使わず `TextScaler.scale()` を通す**（[F] §5.10）。

**[ベンダー]** Flutter に**縦書き・ルビ・`word-break`/`line-break` 相当は存在しない**（[F] §5.11）。
行頭禁則は ICU の UAX#14 が効くが、**長音符「ー」と小書きかな「っ ゃ」は行頭に来る**（`line-break: normal` 相当）。
`strict` に切り替える手段は無い。→ **ルビが必要になったら自作が確定。**

---

## 4. スペーシングと角丸

### 4.1 スペーシング

```
--space-1: 0.25rem   --space-2: 0.5rem   --space-3: 0.75rem
--space-4: 1rem      --space-6: 1.5rem   --space-8: 2rem
```

> **未回答（重要）**: **8pt グリッド／スペーシングスケールの根拠は存在しない。**
> [L] §6-15 が「4パス通じて一次ソースに到達できず」と明記している。
> 上記は **慣習**として採用しているだけで、根拠のある数値ではない。
> [W] §5-4 の「余白のスケール、特に日本語UIでの検証は誰もしていない」も併せて残っている。
> **「8の倍数だから正しい」という説明をしない。**

### 4.2 角丸は単一の `--radius` から倍率で導出

**[1社DS]** shadcn/ui の出荷コード（`apps/v4/app/globals.css`）そのまま（[W] §3.2）。既定 `--radius: 0.625rem`:

```css
--radius-sm:  calc(var(--radius) * 0.6);
--radius-md:  calc(var(--radius) * 0.8);
--radius-lg:  var(--radius);
--radius-xl:  calc(var(--radius) * 1.4);
--radius-2xl: calc(var(--radius) * 1.8);
```

> **2025年頃のブログに広く出回っている `calc(var(--radius) - 4px)` 系の px オフセット版は使わない**
> （`--radius: 0` で負値になる）。倍率版が現行（[W] §3.2）。

`Flutter:` 同じ倍率関係を定数で持つ。**現行実装は 16 / 12 / 10 / 20 が各ファイルに散っている**ので集約する。

### 4.3 ターゲットサイズ

**[W3C]** WCAG 2.2 SC 2.5.8 は **24 CSS px**。**サイズだけでなく「間隔」でも満たせる**（[W] §2.3）:

> "if a **24 CSS pixel diameter circle is centered on the bounding box** of each, the circles do not intersect another target"

一次ソースの作例: 24×24 → 適合 / 20×20 + 間隔4px → **適合** / 20×20 + 間隔なし → 不適合。

**適用範囲の注意**（[W] §2.3）: 「中心間24px」が使えるのは**隣接要素も24px以下のとき**。
大きなターゲットに隣接する場合は、小ターゲットの中心から大ターゲットの最近接エッジまで **12 CSS px 以上**。
サイズ混在の行では円判定を使う。

> **「24px が AA の下限で 44px は AAA の任意目標」という主張は否決済み**（[W] §4-c）。書かない。
> **タッチ運用の実用サイズについて参照文書は根拠を持たない。** 24px は法的下限として扱う。

**[ベンダー]** プラットフォーム推奨は Android **48dp**、Apple **44pt**。
**どちらを満たしても WCAG の 24 CSS px は自動的に満たす**（物理換算 48dp≈7.62mm / 44pt≈6.86mm / 24px≈6.35mm。[L] §1.2）。

**採用**: 出欠を選ぶボタン（主要操作）は **48dp / 48px 以上**。それ以外は 24 CSS px の円判定で検証。

**[コンサル]** 危険な操作を他から離して置く根拠は**到達性ではなく誤タップ防止**。
Hoober 本人が「危険な操作を届きにくい左上へ」を明確に否定している（"**But I wouldn't recommend that.**"）一方、
2017年版は "Account for mistakes by placing dangerous or unrelated items far from other items" として別根拠で推奨している（[L] §1.1）。

---

## 5. モーション

### 5.1 アニメーションは `transform` と `opacity` に限定する

**[ベンダー]** web.dev（[L] §3.2）:

> "Where possible, **restrict animations to `opacity` and `transform`** to keep animations on the compositing stage of the rendering path."

**[ベンダー] + [規範的機構]** `transform` による移動は **CLS に計上されない**。
web.dev の記述に加え、WICG Layout Instability がメトリクス定義そのもので
"**transform-indifferent starting point**" を定義している（[L] §3.2）。

**逆側の規則も同じ記事にある（こちらを見落としやすい）**:

> "**Changing the `top` and `left` properties also cause layout shifts, even when the element being moved is on its own layer.**"

→ **「独自レイヤに載せたから大丈夫」は CLS に対する防御にならない。**

`Web:` **現行 `style.css:36-42` の `.highlight-row` は `background-color` を 2秒アニメーションしている。**
`background-color` は compositing 段に乗らないため毎フレーム paint が走る。
**`transform`/`opacity` で表現できる形（例: 疑似要素のオーバーレイを `opacity` でフェード）に置き換える。**

> **未回答（数値を発明しない）**: 「値が変わったことの伝え方（フラッシュ／ハイライト）の**推奨持続時間**」と
> 「多数が同時に変化したときの視覚ノイズ許容量」は [W] §5-3 で未回答。
> **現行の 2秒を別の数値に置き換える根拠は無い。** 直すのは**プロパティの選択**であって持続時間ではない。

**[ベンダー]** `will-change` はスタイルシートに常時書かない。
"**Don't apply `will-change` to too many elements.**" / 変化の直前だけ JS で付け、終わったら外すのが good practice（[L] §3.2）。

### 5.2 閾値

**[ベンダー]** Core Web Vitals（Google 定義のフィールドメトリクス。**W3C 規範でも WCAG でもない**。[L] §3.2）:

| メトリクス | Good | Poor |
|---|---|---|
| INP | ≤ 200ms | > 500ms |
| CLS | ≤ 0.1 | > 0.25 |

測定定義とセットでないと意味がない: **フィールドデータの75パーセンタイル**、モバイル/デスクトップ分離。
Lighthouse の単発ラボ実行には適用されない。

**[コンサル]** ローディング表示の閾値（NN/g、根本の3閾値は 1968年 Miller 由来。[F] §7.4）:

| 待ち時間 | 表示 |
|---|---|
| 1秒未満 | **ローディング表示自体が不要** |
| 2〜10秒 | スピナー / スケルトン |
| 10秒超 | 進捗バーが強く推奨 |

> **スケルトンが体感速度を上げるという主張は一次ソースが割れている**（[F] §7.4）。
> **「進捗アニメで体感11〜12%短縮」は要注記扱いで、日本の中高生・モバイルUIへ外挿する根拠がない**（[F] §7.4）。

**さくら CGI の実測は 0.6〜1.1秒/リクエスト**（`attendance-tools\SAKURA_SETUP.md`）。
**1秒未満が大半なので、ページ遷移にスケルトンを足さない。**

### 5.3 再取得でちらつかせない

**[ベンダー]** TanStack Query の状態モデルが設計指針になる（[W] §3.4）。
`status`（データがあるか）と `fetchStatus`（クエリが走っているか）は**直交**していて、
データが一度入れば `status` は `pending` に戻らない。

- **スケルトンは初回だけ**
- 以降は既存データを残したまま、控えめな「更新中」を重ねる
- 要素を**アンマウントしない**

> 表現の精度: これは「公式に義務づけられている」のではなく「API の状態モデル上これが自然」。
> docs は "sometimes you may want to" という許容的表現（[W] §3.4）。

### 5.4 モーション低減

`Web:` **[W3C]** `prefers-reduced-motion` を尊重する。

`Flutter:` **[ベンダー]** **`MediaQuery.disableAnimationsOf(context)` は Android 専用。**
iOS の「視差効果を減らす」では true にならず、
**`PlatformDispatcher.accessibilityFeatures.reduceMotion` を別途見る必要がある**（[F] §4.3）。
**2つの口から取る。**

### 5.5 Flutter の duration / easing は自作しない

**[ベンダー]** `packages/flutter/lib/src/material/motion.dart` は Material のトークン DB から**自動生成**されており、
**M3 仕様そのものと同一視してよい**（[F] §4.1）。

```dart
Durations.short2   // 100ms
Durations.short4   // 200ms
Durations.medium2  // 300ms
Durations.long2    // 500ms
Easing.standard              // Cubic(0.2, 0.0, 0.0, 1.0)
Easing.emphasizedDecelerate  // Cubic(0.05, 0.7, 0.1, 1.0) — 画面内に入ってくる要素用
```

**採用**: 出欠の選択反映は `Durations.short2` + `Easing.standard`（繰り返し起きる操作）。
画面に入ってくるシートやダイアログは `Easing.emphasizedDecelerate`。

> **Material 3 Expressive は Flutter に存在しない**（[F] §1.4、Issue #168813 で
> "we are not actively developing Material 3 Expressive" と明言）。使おうとしない。
> **「M3 のモーション duration トークンは 50–1000ms の16段階」という主張は否決済み**（[L] 第5部-j）。
> 上に書いた値は Flutter の実コードから取ったもの。

---

## 6. 禁止事項

| # | 禁止 | 理由 |
|---|---|---|
| 1 | **Liquid Glass**（`liquid_glass_widgets` / `glass_theme.dart` 一式） | 目指す方向と逆。加えて **[ベンダー]** Impeller は **iOS で Skia に戻せない**ため、重いブラー・`saveLayer` 多用は退避路が無い（[F] §1.2 / §1.6） |
| 2 | **カラーグラデーション背景**（`gradient_background.dart`） | ソリッドな面で階層を作る。グラデは面の境界を曖昧にしコントラスト検証を不能にする |
| 3 | **過剰彩度**（現行 `saturation: 1.6`） | **[ベンダー]** Material 2: 彩度の高い色は暗い背景に対し "**optical vibrations**" を生み眼精疲労を招く（[L] §3.3） |
| 4 | **chromatic aberration**（現行 `0.025`） | 文字の輪郭に色ずれを作る。コントラスト比の前提を壊す |
| 5 | **色のみによる状態表現** | **[W3C]** SC 1.4.1 Level A 違反。アイコン形状 + テキストを常に併記（§2.3） |
| 6 | **本文 14px 未満** | **[公的機関]** DADS「14 CSS px未満の大きさの使用は原則として許容されません」（§3.1） |
| 7 | `background-color` / `top` / `left` のアニメーション | **[ベンダー]** paint / layout を誘発。`transform`・`opacity` を使う（§5.1） |
| 8 | Astro UXDS の色を白背景のテキストに流用 | **[1社DS]** Astro 自身が「ライトの塗りは AA を満たさない」と明記（§2.4） |
| 9 | `--radius` の px オフセット版 | `--radius: 0` で負値になる（§4.2） |
| 10 | Flutter で `Opacity` ウィジェットをアニメーションさせる | **[ベンダー]** 公式ベストプラクティスが名指しで回避を指示（[F] §1.6） |

---

## 7. アクセシビリティの実装規約

### 7.1 フォーカス

**[機械可読]** `:focus-visible` は **Baseline Widely available（2022年3月）**。`@supports` 不要（[L] §2.2）。

**[W3C]** フォーカスインジケータのコントラスト根拠は **SC 1.4.11 Non-Text Contrast（3:1）**。
**SC 2.4.13 Focus Appearance は AAA で測定軸も別物**なので混同しない（[L] §2.2）。

```css
:where(button, a, [role="button"], input, select):focus { outline: none; }
:where(button, a, [role="button"], input, select):focus-visible {
  outline: 2px solid var(--ring);   /* 隣接背景に対し 3:1 以上 */
  outline-offset: 2px;
}
```

> **落とし穴**: **スクリプトによる `focus()` では `:focus-visible` にマッチしない**ことがある。
> Selectors 4 では直前のインタラクションの focus-visible 状態を継承するため、
> **マウスクリックで開いたダイアログにスクリプトでフォーカスしても Chrome/Firefox では光らない**（[L] §2.2）。
> 「モーダルを開けばリングが出る」を前提にしない。明示的に描くか実測する。

### 7.2 sticky 要素

**[W3C]** SC 2.4.11 Focus Not Obscured (Minimum) は **Level AA**。規範文は
"the component is **not entirely hidden**"。**部分的な被覆は AA では合格する**（Understanding が明記）。
SC 2.4.12（AAA）が "**no part**" を要求する（[L] §2.3）。

sticky header / sticky footer が名指しで挙げられている。合格テクニックは scroll padding:

```css
:root { --app-header-h: 56px; }
html { scroll-padding-block-start: var(--app-header-h); }
.table-scroll { scroll-padding-block-start: var(--table-thead-h); }
```

### 7.2.1 テーブルの見出しセル

**[W3C]** 2次元テーブル（ユーザー × 活動）の**行見出しは `<th scope="row">`**、列見出しは `<th scope="col">`。
**`<td>` を見出しに使わない**（**SC 1.3.1 Info and Relationships / Level A**）。
行見出しが `<td>` のままだと、セル単独では「誰の」出欠か読み上げから判別できない。

`Web:` **現行 `style.css:20-26` の `.sticky-col`（横方向 sticky）を SC 2.4.11 に照らして検証する。**
被覆が「完全」かどうかで AA 判定が変わる。**加えて半透明・ぼかしのオーバーレイは
"may separately fail 1.4.11 Non-text Contrast" と注記されている**（[L] §2.3）ため、`.sticky-col` は不透明な面にする。

### 7.3 破壊的操作

**[コンサル]** NN/g の3規則（実証データなし。[L] §2.6）:

> "Use a confirmation dialog before committing to actions with **serious consequences**"
> "**Do not use confirmation dialogs for routine actions.**"
> "provide **response options that summarize what will happen**" — 例: `Delete file` / **`Keep file`**

**通説より具体的な点2つ**: 規定は「動詞にせよ」ではなく「**何が起きるかを要約する語にせよ**」。
**キャンセル側も結果で書く**（"Cancel" ではなく "Keep file"）。

**[非規範 APG]** 破壊的確認ダイアログの初期フォーカスは**破壊しない方**に置く（[L] §2.6）:

> "it **may be advisable to set focus on the least destructive action**"

APG 自身の実例が "No" ボタンにフォーカスを当てている。**推測ではなく明文**（ただし "may be advisable" ＝推奨）。

**[1社DS]** type-to-confirm を使うなら**既定のトークンは固定語 `confirm`**。
**「リソース名を打たせる」変種はどこにも支持されていない**（Cloudscape / PatternFly。[L] §2.6）。
適用は「高severityの削除」に限定。

本システムでの適用:

| 操作 | 確認 |
|---|---|
| 出欠の変更 | **確認しない**（routine action。NN/g の「cry wolf」規定） |
| イベント削除 | 確認ダイアログ。ボタンは `イベントを削除` / `削除しない` |
| ユーザー削除 | 確認ダイアログ + 初期フォーカスは「削除しない」 |
| DB バックアップ削除など高severity | 現状該当なし。増えたら固定語 `confirm` の入力を検討 |

> **未回答**: destructive ボタンの**左右配置**、モーダルを閉じた後の**フォーカス復帰先**は
> [L] §6-9 / §6-10 で未回答。**推測で決めず、実装時に別途調査するか慣習に従うことを明記する。**

### 7.4 キーボードショートカット

**[W3C]** 修飾キーなしの単一文字ショートカットは **SC 2.1.4 Character Key Shortcuts（Level A）** の対象。
**連続キー（`g` → `i` 方式）も対象**、`?`（Shift+/）も対象（[L] §2.1）。
実装するなら「無効化できる」「再マップできる」「フォーカス時のみ有効」のいずれかが必要。

> **`Cmd+K` のような修飾キー付きの扱いは断定して書かない**（[L] §2.1、当該主張は 1-2 で否決）。
> **正しくは「Level A の規範的 W3C 要件」**。米 Section 508 の義務ではない（WCAG 2.0 参照のため）が、
> EU の EN 301 549 には含まれる。

**本システムでは当面ショートカットを実装しない。** 中高生の非専門家利用でメリットが薄く、規制対応のコストが上回る。

### 7.5 Flutter 固有

**[ベンダー]** **`SemanticsService.announce` は v3.35.0-0.1.pre 以降 deprecated**。
Android では **TalkBack の読み上げキューを破壊する**ため公式に非推奨（[F] §6.7）。使わない。

**[W3C]** 正誤・状態を色だけで伝えるのは SC 1.4.1 違反になりうる。アイコンかテキストを必須（[F] §6.7）。

**[ベンダー]** UI レイヤの import は**1ファイルに集約して re-export する**。
Material / Cupertino は 3.44 でコアから凍結され `material_ui` / `cupertino_ui` へ移行中（[F] §1.1）。
**ただし移行は急がない** — `package:flutter/material.dart` はまだ非推奨警告を出しておらず、
`material_ui` は **0.0.2（pre-1.0、本番不可）**。今やるのは import の集約だけ。

---

## 8. この文書で決めていないこと（未回答の一覧）

**推測で埋めない。** 必要になったら別途調査する。

1. **日本語UIの行間・字間の最適値** — DADS の離散スケールはあるが「どれが最適か」の根拠は無い（[W] §5-4 / [F] §9-4）
2. **8pt グリッド／スペーシングスケールの根拠** — 4パス通じて一次ソース未到達（[L] §6-15）
3. **値の変化を伝えるハイライトの持続時間**と、多数同時変化時の視覚ノイズ許容量（[W] §5-3）
4. **destructive ボタンの左右配置**、**モーダル閉鎖後のフォーカス復帰先**（[L] §6-9 / §6-10）
5. **楽観的UI**の扱い（[W] §5-2）
6. **コンテナクエリの実務採用状況** — ビューポート基準との役割分担（[W] §5-5）
7. **`text-wrap: balance` / `pretty` の日本語での実挙動** — MDN に記述が無い（[L] §6-17）
8. **`clamp()` に `rem` を混ぜて SC 1.4.4 の失敗を避ける実装法**の一次記述（[L] §6-18）
9. **`font-feature-settings: "palt"` の実務**（[L] §6-19）— Flutter 側は実測あり（[F] §5.6）だが Web 側は未確認

---

## 9. 参照文書と鮮度

| 文書 | 調査日 | 本書が依拠した主な章 |
|---|---|---|
| `web-design-2026.md` | 2026-07-29 | §1 ステータス設計 / §2 色とA11y / §3 実装の型 |
| `latest-ui-ux-insights.md` | 2026-07-29 | §1 モバイル / §2 コンソール / §3 CSS・CWV・ダーク / §4 日本語タイポ |
| `flutter-app-ui-2026.md` | 2026-07-29 | §1 土台 / §4.1 モーション / §4.3 触覚と低減 / §5 日本語組版 / §7 起動 |

**腐りやすい項目**（引くときは取得日を併記する）:
- **Baseline ステータス** — `light-dark()` は最速 2026-11、`content-visibility` は最速 2028-03 に Widely へ移行（[L] §3.1）
- **Flutter の版数** — 四半期ごとに stable が出る。[F] の実測は **3.41.9 / Noto Sans JP 2.004-H2**。
  実装前に `flutter --version` で確認し、**行箱は再測する**（[F] §10）
- **Astro UXDS は保守終了**。値と分類法は有効だが「2026年のトレンド」の証拠には使えない（[W] §6）

**一次ソースと適用先のギャップ**（両文書が明記している。忘れない）:
Carbon / PatternFly / Cloudscape / Apple / Google はいずれも**英語圏の大規模プロダクト向け**で、
**日本語UI・非専門家・短時間利用**という条件での妥当性は各システムが検証していない。
日本語圏の一次ソースは **DADS のみ**。

---

## 10. 変更履歴

| 日付 | 内容 |
|---|---|
| 2026-07-30 | 初版。フェーズ0（共通デザイン言語の確定）。実装はまだ行っていない |
| 2026-07-30 | 合意。§1.3 に面・テキストのトークン確定値と `--highlight-flash` を追加（ステータス色を状態と無関係な演出へ流用しないため独立させた）。§7.2.1 にテーブル見出しセルの規約（`<th scope>`）を追加。フェーズ1（Web）の実装を開始 |
| 2026-07-31 | フェーズ2（Flutter）実装。§1.3 に `--border-strong` を追加（入力欄の枠は SC 1.4.11 の 3:1 対象だが `--border` は 1.35:1 しかない）。Flutter は `AppColors` ThemeExtension で §2.4 の値を持ち込み、Liquid Glass とグラデーション背景を撤去。Web にも `--border-strong` を反映 |
