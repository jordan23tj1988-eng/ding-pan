---
name: "gsap-skills"
description: "GSAP动画官方skill(greensock/gsap-skills)：教AI正确使用GSAP——core/timeline/ScrollTrigger/plugins/utils/react/performance/frameworks八模块。写GSAP动画、滚动动画、parallax、hero动效(含finesse-ui的GSAP引擎路线)或用户提到\"gsap/ScrollTrigger/滚动动画\"时使用;完整模块在D:\\skill\\gsap-skills"
---

# GSAP Skills — GreenSock官方AI技能包

> 来源：https://github.com/greensock/gsap-skills （GreenSock官方，9.7k★）
>
> **⚠️ 文件位置**：完整模块在用户本机 `D:\skill\gsap-skills\`（8个模块目录各含SKILL.md + `llms.txt`索引 + `examples/`参考demo）。**本文件只是路由索引——确认 D:\skill 已挂载后，按下表用 Read 读取对应模块的 SKILL.md 再写码**，不要凭训练数据里的旧GSAP用法直接写。

## 重要背景

GSAP 自被 Webflow 收购后**完全免费**（含全部插件）。原 Club GSAP 付费插件（SplitText、MorphSVG 等）现在都免费可商用，直接从公开 npm 包安装：`npm install gsap`，**不需要** `.npmrc`/auth token/私有 registry。浏览器直接用时可从 CDN 引入或本地内联 `gsap.min.js`（finesse-ui 的 examples/lib/ 里就有本地副本）。

## 模块路由表（按需 Read `D:\skill\gsap-skills\<模块>\SKILL.md`）

| 模块 | 何时加载 | 触发词 |
|------|---------|--------|
| `gsap-core` | 基础动画：`gsap.to/from/fromTo()`、easing、duration、stagger、defaults、transforms、autoAlpha、`gsap.matchMedia()`（响应式 + prefers-reduced-motion） | animation library, tweens, easing, stagger, reduced motion |
| `gsap-timeline` | 多步编排：`gsap.timeline()`、position参数、labels、嵌套、播放控制 | sequencing, timeline, keyframes, 多步动画 |
| `gsap-scrolltrigger` | 滚动驱动：scroll-linked动画、pinning、scrub、triggers、refresh、cleanup | scroll animation, parallax, pin, scrub |
| `gsap-plugins` | 插件：ScrollToPlugin, ScrollSmoother, Flip, Draggable, Inertia, Observer, SplitText, ScrambleText, MorphSVG/DrawSVG/MotionPath, CustomEase, GSDevTools | plugin, flip, draggable, SVG drawing, SplitText, registerPlugin |
| `gsap-utils` | 工具函数：clamp, mapRange, normalize, interpolate, random, snap, toArray, wrap, pipe | gsap.utils |
| `gsap-react` | React：`useGSAP` hook、refs、`gsap.context()`、cleanup、SSR | React animation |
| `gsap-frameworks` | Vue / Svelte / 其他框架集成 | Vue animation, Svelte |
| `gsap-performance` | 性能：只动 transform/opacity、force3D、批量读写、ticker | 卡顿, jank, 60fps |

## 使用规则

1. **先读再写**：命中触发词后，Read 对应模块的 SKILL.md，按其中的当前版本API和最佳实践写码；多个模块相关就读多个（如"滚动序列动画"= scrolltrigger + timeline）。
2. **与 finesse-ui 配合**：finesse 的 hero 引擎选到 GSAP ScrollTrigger 路线时，设计骨架听 finesse（`D:\skill\finesse-ui\references\hero-engines.md`），API 写法听本skill的 gsap-scrolltrigger/gsap-core 模块。finesse 的动效纪律不可违背：只动 `transform`/`opacity`、`prefers-reduced-motion` 必须有降级、动机化动效、每页最多一个 marquee。
3. **无障碍**：任何 GSAP 动画都配 `gsap.matchMedia()` 的 `(prefers-reduced-motion: reduce)` 分支（gsap-core 模块有标准写法）。
4. **验证**：GSAP 页面 weasyprint 出图看不到动画（不执行JS）——需要用 playwright 无头浏览器截图或让用户浏览器打开验证。
5. `examples/` 目录（`D:\skill\gsap-skills\examples\`）有 vanilla JS 和 React 的最小参考 demo，写复杂动画前可先看对应示例。
