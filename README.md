# こま名刺ページ（Coma Days）

名刺の QR コードから開く 1 枚ページ。

1. 開いた瞬間、こまが走って寄ってくる動画（`coma-run.mp4`）が全画面で再生される
2. こまが近くまで来たタイミング（動画終了の 1.5 秒前）でリンク欄がふわっと出る
3. リンク欄の表示中は、背景がこまの写真集になり 2〜3 秒ごとにランダムで切り替わる

## ファイル構成

| ファイル | 役割 |
| --- | --- |
| `index.html` | ページ本体 |
| `style.css` | 見た目 |
| `script.js` | 動画→リンク欄の切り替え／写真集の制御。**設定は先頭のブロックだけ** |
| `coma-run.mp4` | オープニング動画（元ファイル名: 寄ってくるこま（AI）.mp4） |
| `photos/coma-01.jpg` 〜 | 背景の写真集（Web 用に縮小済み） |
| `ogp.jpg` | SNS でシェアしたときのサムネイル |
| `tools/build_photos.py` | 元写真を Web 用に一括変換するスクリプト |

## リンクを変える

`script.js` の先頭にある `LINKS` の `url:` を書き換えるだけ。

```js
const LINKS = [
  { title: "Instagram", sub: "こまの写真と日常", url: "https://www.instagram.com/xxxx", ... },
];
```

- 増やしたいときは `{ ... }` を同じ形でコピーして追記
- 減らしたいときは `{ ... }` を行ごと削除
- `icon` に指定できるのは `instagram` / `tiktok` / `line` / `link`（汎用）

## 写真を追加・差し替えする

元写真（フルサイズ）を 1 つのフォルダにまとめて、次を実行すると `photos/` が作り直される。

```bash
python tools/build_photos.py "C:\Users\hm-miyashita\Desktop\宮下\実験\coma"
```

- 長辺 1600px / JPEG 品質 78 に縮小（22 枚で 87MB → 4.1MB）
- iPhone 写真の回転情報を反映したうえで、**GPS を含む Exif は削除**される
- 枚数が変わったら `script.js` の `PHOTO_COUNT` も合わせて変更する

## 公開

GitHub Pages（`Settings > Pages > Branch: main / root`）。
公開 URL は `https://miyasita384.github.io/pagu.github.io/`。

## 動作の細かい設定（`script.js` 先頭）

| 定数 | 意味 | 既定値 |
| --- | --- | --- |
| `REVEAL_LEAD` | 動画の終わり何秒前にリンク欄を出すか | `1.5` |
| `FAILSAFE_SEC` | 動画が再生できなかったとき強制的にリンク欄を出す秒数 | `9` |
| `SLIDE_MIN_MS` / `SLIDE_MAX_MS` | 写真の切り替え間隔（この範囲でランダム） | `2000` / `3000` |
| `PHOTO_COUNT` | `photos/` に入っている写真の枚数 | `22` |
