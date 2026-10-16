<p align="center">
  <img src="assets/hero.svg" width="100%" alt="Samprith C Amin. A live pressure-sensor heatmap: footprints walk across a 14 by 96 cell mat and a line cross is detected.">
</p>

<p align="center">
  <a href="https://vyanikatech.com"><img src="assets/btn-site.svg" height="46" alt="Website: vyanikatech.com"></a>
  <a href="https://www.linkedin.com/in/samprith-c-amin/"><img src="assets/btn-linkedin.svg" height="46" alt="LinkedIn: samprith-c-amin"></a>
  <a href="mailto:samprith02@gmail.com"><img src="assets/btn-email.svg" height="46" alt="Email: samprith02@gmail.com"></a>
</p>

## `0x00` boot

<img src="assets/boot.svg" width="100%" alt="Terminal boot log. firmware.service: STM32 and Giga R1 nodes, about 2,700 cells, 120 to 15 ms. server.service: FastAPI and WebSockets on a Raspberry Pi 5 kiosk. browser.service: framework-free JS, Canvas heatmaps, WCAG AA. agents.service: 21 agents, 82 tools, humans approve every write. research.service: FedAvg and FedProx from scratch, 100 clients. student.service: B.E. AI and ML at MITE, class of 2027. Reached target: Co-Founder and CTO, Vyanika Innovations LLP.">

I'm a final-year AI & ML student who co-founded a startup and ended up building every layer it runs on: C firmware on the sensor boards, a Python server on a Raspberry Pi, the browser screen the referee reads, and, on the side, multi-agent LLM systems.

## `0x01` flagship · Tech Kabaddi

<img src="assets/signal-path.svg" width="100%" alt="Tech Kabaddi signal path: pressure mat, embedded firmware, FastAPI and WebSocket server, referee review. End-to-end latency 120 ms down to 15 ms (8 times lower); packet size about 8 KB down to about 200 B (40 times smaller). 243 automated tests, 11 releases in 3 weeks, about 13k lines of Python and JS, WCAG AA contrast.">

Tech Kabaddi is a sensor-based officiating system for kabaddi: pressure mats on the court, firmware that streams every cell, and a review screen that calls the lines. I lead its engineering as CTO of [Vyanika Innovations](https://vyanikatech.com). The source is private.

- **Firmware:** traced false pressure readings to crosstalk from parallel ADC reads and fixed it with sequential row scanning. One codebase configures itself on every node at boot.
- **Server:** NumPy-vectorised packet decoding, a 30 FPS broadcast cap so one slow tablet never holds up the rest, and O(log n) seeks for replay.
- **Browser:** no framework. Binary WebSocket frames are decoded with `DataView` and heatmaps are written pixel by pixel into `ImageData`.
- **Also mine:** the company site (Astro, Lighthouse 100 on desktop) and certificates whose QR codes carry an ECDSA P-256 signature, checked offline at [vyanikatech.com/verify](https://vyanikatech.com/verify).

## `0x02` open source

<p align="center">
  <a href="https://github.com/samprith02/VidyaERP"><img src="assets/card-vidyaerp.svg" width="49%" alt="VidyaERP: agentic ERP for engineering colleges. 21 agents, 82 tools, timetable solver places 456 of 456 periods with 0 clashes. Python, FastAPI, MCP."></a>
  <a href="https://github.com/samprith02/SETU"><img src="assets/card-setu.svg" width="49%" alt="Setu: MCP server that lets an AI agent buy over Razorpay test-mode rails inside a spend mandate. 5 MCP tools, 59 tests. Node.js, Express, Razorpay API."></a>
</p>
<p align="center">
  <a href="https://github.com/samprith02/ML-Research-Federative-sim"><img src="assets/card-fedlearn.svg" width="49%" alt="Federated learning research: FedAvg and FedProx from scratch, 100 simulated clients on CIFAR-10. FedProx beats FedAvg by 14.5 points at alpha 0.1. Python, PyTorch."></a>
  <a href="https://github.com/samprith02/chronos-teacher-erp-timetable"><img src="assets/card-chronos.svg" width="49%" alt="Chronos: teacher ERP and timetable engine with MRV backtracking and hill-climbing. About 6k lines of TypeScript, 21 React components. Next.js."></a>
</p>

## `0x03` scoreboard

| result | where |
| :-- | :-- |
| 🥇 **1st of 130 teams** | NAIN 2.0 (2025), Govt. of Karnataka: ₹5 Lakh grant and K-Tech NAIN incubation |
| 🥇 **1st prize** | NAIN Innovation Conclave 2026 at IIIT Bangalore, prototype demonstration |
| 🏆 **Winner** | BOLPU, the Dakshina Kannada MP's startup programme; the only student-led team |
| 🚀 **Incubated** | AIC IIT Delhi (Sonipat campus) |
| 🎯 **Top 50 nationwide** | NSRCEL pre-incubation, IIM Bangalore |
| 🏁 **Finalist** | Elevate, Govt. of Karnataka |
| 🧪 **Semi-finalist** | Elevate NxT 2026 (DeepTech), Govt. of Karnataka, from 983 applicants |
| 📜 **Patent filed** | Indian application 202641005974, Integrated Smart Kabaddi Mat System (co-inventor) |

## `0x04` toolbox

| layer | what I use |
| :-- | :-- |
| **silicon** | `C` `C++` `STM32` `Arduino Giga R1` `ESP32` `Raspberry Pi 5` |
| **server** | `Python` `FastAPI` `Node.js` `Express` `WebSockets` `NumPy` |
| **data** | `MySQL` `MongoDB` `SQLite` |
| **browser** | `JavaScript` `TypeScript` `React` `Next.js` `HTML` `CSS` `Astro` `Tailwind CSS` `GSAP` `Canvas 2D` |
| **agents & ML** | `LLM tool calling` `multi-agent systems` `MCP` `PyTorch` |
| **shipping** | `Git` `GitHub Actions` `pytest` `Playwright` `Linux` `systemd` `Figma` `Claude Code` |

<p align="center">
  <img src="assets/footer.svg" width="100%" alt="A pressure trace of footfalls. End of packet. CRC16-CCITT of samprith02 is 0x157A.">
</p>

<!-- Every image above is generated by tools/make_assets.py (python tools/make_assets.py). -->
