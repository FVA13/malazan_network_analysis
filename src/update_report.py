import re

import yaml
import typer
from pathlib import Path
from loguru import logger

from src.config import REPORTS_DIR
# from config import REPORTS_DIR

app = typer.Typer()


@app.command()
def main(reports_dir: Path = REPORTS_DIR):
    logger.info("Begin analysis_report.md update")

    # Read results
    with open(reports_dir / 'results.yaml', 'r') as f:
        results = yaml.safe_load(f)

    # Read markdown template
    with open(reports_dir / 'analysis_report_template.md', 'r') as f:
        markdown = f.read()

    # Replace placeholders
    for key, value in results.items():
        placeholder = f'${{{key}}}'
        if placeholder in markdown:
            logger.info(f"'{placeholder}' placeholder found!")
        else:
            logger.warning(f"'{placeholder}' placeholder not found in markdown")
        markdown = markdown.replace(placeholder, str(value))

    # Replace table placeholders
    table_pattern = r'%{(table_[^}]+)}'
    tables = re.findall(table_pattern, markdown)

    for table_id in tables:
        table_file = reports_dir / 'figures' / f'{table_id}.md'
        if table_file.exists():
            with open(table_file, 'r') as f:
                table_content = f.read().strip()
                # Indent each line of the table content by 4 spaces
                indented_table = '\n'.join('    ' + line for line in table_content.split('\n'))
                # Add newline after the table while maintaining indentation for following content
                formatted_content = f"\n{indented_table}\n"
            markdown = markdown.replace(f'%{{{table_id}}}', formatted_content)
        else:
            logger.warning(f"Table file not found: {table_file}")

    # Write updated markdown
    with open(reports_dir / 'analysis_report.md', 'w') as f:
        f.write(markdown)

    logger.success("analysis_report.md updated")


if __name__ == '__main__':
    app()
