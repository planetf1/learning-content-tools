# IBM Quantum Learning content tools

Scripts and actions to help maintainers of IBM Quantum Learning content.


## Syncing with Directus

To sync your notebooks automatically with the Directus database, you'll need to
add a `directus_info.json` to the same folder as each notebook.

```json
# directus_info.json
# This goes in the same folder as your notebook
{
  "STAGING": {
    "url": "https://learning-api-dev.quantum-computing.ibm.com",
    "id": "o4845b0b-1acc-4q73-b93b-9f7cbcbb552a"
  }
}
```

To upload notebooks using our script:

1. Install the package
   ```bash
   pip install git+https://github.com/frankharkins/learning-content-tools/iql-notebook-sync
   ```
2. Run this from the root of your content folder:

   ```bash
   sync-notebooks path/to/notebook
   ```
   You'll be prompted for your username and password.

To use this script as part of CI (Travis / GitHub actions), set the
`DIRECTUS_TOKEN` environment variable to your access token before running the
script.
