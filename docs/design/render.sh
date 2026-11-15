#!/usr/bin/env bash
# Renders every PlantUML model in docs/design to PNG and SVG.
# Needs Java and Graphviz (dot). Download plantuml.jar from https://plantuml.com/download
# and set PLANTUML_JAR, or put it next to this script.
set -euo pipefail
cd "$(dirname "$0")"
JAR="${PLANTUML_JAR:-./plantuml.jar}"
for dir in arch class sequence; do
  java -Djava.awt.headless=true -jar "$JAR" -tpng "$dir"/*.puml
  java -Djava.awt.headless=true -jar "$JAR" -tsvg "$dir"/*.puml
done
echo "Done."
