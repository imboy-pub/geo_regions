# geo_regions Demo / 交互原型

## 中文

本目录让计划第一节点先看到可交互界面。它包含两种实现：

| 目录 | 用途 | 本轮状态 |
|---|---|---|
| `flutter/` | Flutter SDK-only 原型、十语主界面标签、5 个 Widget 测试 | 已写源码；执行环境没有 Flutter/Dart，未编译、未跑 Widget 测试，尚需 `dart format` |
| `web_preview/` | 双击即可打开的独立 HTML 交互参考 | 22 项 Node 行为检查通过；本轮 Chromium 进程受限，云浏览器亦拒绝 file 协议；未完成视觉验收 |

两个实现均使用小型、确定性的手工演示数据。**它们没有调用生产 `geo_regions` SDK，也没有真正下载网络资源。** 默认中国为“随包离线”示例，其他国家为“模拟在线”示例；下载后的缓存只存在当前页面或进程的内存中，刷新或重启会清除。`data/` 中的真实国家结构和语言包另有覆盖报告，不要用这里的 fixture 数量计算数据覆盖率。

### 先看效果

用浏览器打开 `web_preview/index.html`。无需启动服务、无需联网或安装 npm 依赖。

建议按以下顺序体验：

1. 中国 → 广东省 → 深圳市 → 南山区。
2. 切换 English / 日本語 / العربية，观察 ID 路径不变和阿语 RTL 排版。
3. 确认选择，再选择其他地区，体验“尚未确认”与放弃修改。
4. 开启“模拟离线”，第一次选择日本，看到明确加载错误；关闭后重试。
5. 再开启“模拟离线”，已下载过的日本仍可使用。
6. 用不存在的名称搜索，观察空结果；使用“演示加载失败”检查重试。
7. 切换深色模式；把窗口缩小到手机宽度检查国家横向选择栏。

### 运行 Flutter

在已安装 Flutter stable 的机器上：

```bash
cd demo/flutter
bash bootstrap.sh
dart format lib test
flutter analyze --fatal-infos
flutter test
flutter run -d chrome
flutter build web --release
```

`bootstrap.sh` 只在 `web/` 缺失时在临时目录生成 Flutter Web 平台文件，再复制 `web/`；它保留本目录的 `pubspec.yaml`、源码和测试。脚本不会打开浏览器或启动长期运行进程。Dart 格式化生成的改动应在提交前保留，不能为了绿色 CI 放宽格式检查。

**以上是现场验收命令，并非本轮已通过的结果。** 首节点只有在执行并保存通过证据后才能标为完成。建议使用 CI 固定的 Flutter 版本，避免本地和 CI 漂移。

### 无外部依赖的行为检查

```bash
node demo/web_preview/test_logic.cjs
```

该检查使用 Node 标准库和极小 DOM 替身验证状态、事件与输出契约；它不验证字体、布局、浏览器兼容性或 Flutter。完整的第一节点验收见 `docs/DEMO_UX.md`。

## English

This directory makes the first plan milestone visibly interactive. `flutter/` is an SDK-only Flutter prototype with ten-language primary UI labels and five Widget tests. `web_preview/` is a self-contained HTML reference that opens without a server or network access.

Both implementations use small, deterministic, hand-curated fixtures. **Neither implementation invokes the production SDK or downloads real resources.** China represents bundled offline data; other countries simulate remote loading. The cache is in memory only and disappears on reload/restart. Production dataset coverage is reported separately under the delivery's data documentation.

The current environment has no Flutter/Dart SDK. Flutter formatting, analysis, tests and compilation were not run. Local Chromium startup was blocked by the execution environment, and direct file-protocol opening in the supported cloud browser was denied by its security policy. Browser visual verification remains pending. Twenty-two dependency-free Node behavior checks passed; those checks are not evidence of browser rendering or Flutter execution.

Run the commands above on a machine with Flutter stable, keep the formatter changes, and record the evidence before marking the first milestone complete. `bootstrap.sh` generates only the missing Web platform directory and preserves the authored sources, tests and SDK-only manifest.

注 / Note: 自有标签覆盖十语，但 Flutter 框架内建文案仍使用默认英文 MaterialLocalizations；完整系统文案本地化和真实读屏验收尚未完成。Custom labels cover ten languages, while built-in Flutter Material copy remains in supported default English; complete framework-copy localization and actual screen-reader acceptance are still pending.
