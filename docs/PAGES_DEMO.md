# 演示站部署 / Demo site deployment

## GitHub Pages（主站）

- URL：`https://imboy-pub.github.io/geo_regions/`
- `/` = Flutter web demo（release 构建，`--base-href /geo_regions/`，P1-01 验收的交互 demo）
- `/preview/` = 自包含静态 UI 原型（`demo/web_preview/index.html`，单文件无依赖）

### 开通步骤（一次性，需仓库管理员）

1. 仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**
2. push 到 `main`（或手动 **Actions → Pages → Run workflow**）即自动构建部署
3. 工作流：`.github/workflows/pages.yml`（构建 → 上传 artifact → deploy-pages；并发组防排队互踩）

本地预演（与 CI 同命令）：

```sh
cd demo/flutter && flutter build web --release --base-href /geo_regions/
cp -r ../web_preview build/web/preview
```

## Gitee（origin，gitee.com/imboy-pub/geo_regions）

Gitee 有对应功能 **Gitee Pages**，但现状须知（2026-01）：

- 免费版 Gitee Pages 服务 **2024-05 起暂停新部署**，是否恢复以 Gitee 官方公告为准；
  仓库页面若显示"Pages 已暂停/需开通"，则该功能当前不可用
- Gitee Pages 需要实名认证，且每次部署**需手动点击更新**（无 webhook 自动化）

### 推荐用法（按可用性分层）

| 场景 | 做法 |
|---|---|
| Gitee Pages 可用 | 把 `demo/flutter/build/web/` 产物推到 gitee 仓库的 `gh-pages` 分支，Pages 设置中选该分支——每次发版手动点"更新" |
| Gitee Pages 不可用（现状大概率） | gitee 仓作为**代码镜像**（origin 已配置），README 放 GitHub Pages 演示链接；不重复部署 |

### 镜像推送（三平台 remote 已配置：github / gitcode / gitee）

```sh
git push github main && git push origin main && git push gitcode main
# 或全部：git push --all
```

> 注意：本机 SSH push 已知 SIGPIPE 问题，建议 HTTPS + credential helper（见项目记忆）。

## 边界说明

- Pages 部署的是 **demo 层**（research 展示），不含正式数据集全集；数据集口径见
  `datasets/csc-candidate/README.md` 与 `docs/UPDATE_RUNBOOK.md`
- demo 使用 research-seed 数据（`data/`），页面已内嵌质量可见性与回退展示
  （P1-01 UX 验收：`?locale=ar&dark=1&semantics=1` 深链可用）

---

## English Summary

Demo site: `https://imboy-pub.github.io/geo_regions/` — `/` serves the Flutter web
demo (release build with `--base-href /geo_regions/`, the P1-01-accepted
interactive demo), `/preview/` serves the self-contained static prototype
(`demo/web_preview/index.html`). Deployment runs in
`.github/workflows/pages.yml` on push to main (or manual dispatch) using the
official upload/deploy-pages OIDC flow; one-time repo setting:
**Settings → Pages → Source = GitHub Actions**.

Gitee has a matching feature (**Gitee Pages**), but the free tier has been
paused for new deployments since 2024-05 (verify on the repo page). Layered
guidance: if available, push `demo/flutter/build/web/` to a `gh-pages` branch
and select it in Pages settings (manual updates per release); otherwise keep
gitee as a code mirror (origin already points there) and link the GitHub Pages
URL from the repo README. SSH push from this machine has a known SIGPIPE
issue — prefer HTTPS + credential helper.

Scope: Pages serves the **demo layer** (research showcase) built from
`data/` (research-seed); dataset layering is documented in
`datasets/csc-candidate/README.md` and `docs/UPDATE_RUNBOOK.md`.
