# IBM Quantum Learning content tools

Scripts and actions to help maintainers of IBM Quantum Learning content.


## Syncing with Directus

To sync your notebooks automatically with the Directus database, you'll need to
add a `directus.conf.yaml` to the root of your content folder.

```yaml
# directus.conf.yaml
# This goes in the root of your content folder
lessons:
 - path: path/to/folder  # path to folder containing the notebook
   # lesson ID in the staging database:
   idStaging: 4e85c04a-c2fb-4bfc-9077-b75bf1b73a25
   # lesson ID in the production database:
   idProduction: 5026731b-5e7b-4585-8cf2-f24482819e21
```

To upload notebooks using our script:

1. Install the package
   ```bash
   pip install git+https://github.com/frankharkins/learning-content-tools.git#subdirectory=iql-notebook-sync
   ```
2. Run this from the root of your content folder:

   ```bash
   sync-notebooks
   ```
   You'll be prompted for your username and password.

You can also upload just one notebook at a time using

```bash
sync-notebooks path/to/folder
```

To use this script as part of CI (Travis / GitHub actions), set the
`DIRECTUS_TOKEN` environment variable to your access token before running the
script.
