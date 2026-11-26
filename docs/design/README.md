# Design Documents

| Folder or file | Content |
|---|---|
| [software-design-report.md](software-design-report.md) | The Software Design Report (includes the NFR mapping to design decisions, tools, and repo paths) |
| [software-design-report.pdf](software-design-report.pdf) | Rendered PDF of the Software Design Report |
| [arch/](arch/) | Architecture diagrams: system deployment (`01-system-architecture`), backend layers (`02-backend-layers`), frontend structure (`03-frontend-structure`) |
| [class/](class/) | Class diagrams: domain model (`01-domain-model`), application routers/services (`02-service-layer`), catalog integration (`03-catalog-integration`), API schemas (`04-schemas`) |
| [sequence/](sequence/) | Sequence diagrams for US-02, 03, 04, 08, 09, 10, 11, 12, 14 and 15 (`01-us02-register` to `10-us14-review`, 67% of the stories) |
| [render.sh](render.sh) | Renders the `.puml` models to PNG and SVG |
| [render-pdf.sh](render-pdf.sh) | Renders the report to the PDF with pandoc and Chromium in Docker, with the style of [report.css](report.css) |

Each model is stored as a PlantUML source file (`.puml`) alongside its rendered `.png` and `.svg` images.
