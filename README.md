# Formula Extractor

Powered by Renoir
Created by igor.goncalves@renoirgroup.com

This module extracts formulas from a hierarchical data structure stored in JSON format.

## Usage

```bash
python formula_extractor.py [options]
```

### Options

- `-i, --input FILE`: Path to the input JSON file (default: tree_data.json)
- `-o, --output FILE`: Path to the output JSON file (default: extracted_formulas.json)
- `-v, --verbose`: Enable verbose output with additional details

### Logging

The module uses the logging system from the `log` package to provide detailed logs for debugging and monitoring. Logs are written to both the console and log files (in the `logs` directory).

The logging configuration can be customized through environment variables:

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_TO_CONSOLE`: Whether to log to console (true/false)
- `LOG_TO_FILE`: Whether to log to file (true/false)
- `LOG_DIR`: Directory to store log files
- `LOG_FILE`: Name of the log file
- `LOG_FILE_MAX_SIZE_BYTES`: Maximum size of the log file before rotation
- `LOG_FILE_BACKUP_COUNT`: Number of backup files to keep

### Example

```bash
python formula_extractor.py -i tree_data.json -o extracted_formulas.json -v
```

## Output Format

The output is a JSON array of objects, each representing an entity with formulas:

```json
[
  {
    "path": "e00078v",
    "formulas": [
      {
        "path": "e00089v",
        "value": "valor_ativo = sum(e00108v, e00083v = 'Sim')",
        "update": {
          "doctype": "Contract Measurement",
          "fieldname": "faturamentodireto"
        }
      },
      // More formulas...
    ],
    "ids": [
      {"id": "0196c4d0-b7ad-7b23-ad96-b316ce979d6f"},
      {"id": "0196c6ad-c158-7883-9b7a-351ef0cf0772"}
    ]
  },
  // More entities...
]
```

## Code Usage

You can also import the module and use it programmatically:

```python
from formula_extractor import extract_formulas
import json

# Load data
with open('tree_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract formulas
results = extract_formulas(data)

# Use the results
print(f"Found {len(results)} entities with formulas")
```# hierarquical_engine
