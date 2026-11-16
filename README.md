# Research Infrastructure Shareable Experiments RO-Crate Profile (RISE RO-Crate Profile)

RISE is an RO-Crate profile for packaging metadata and artifacts of experiments conducted in Research Infrastructures (RIs). RISE artifacts document what was executed, in which environment, and with which results.

- **Profile definition (latest stable)**: https://tumi8.github.io/rise-ro-crate-profile
- **Profile definition (development)**: https://tumi8.github.io/rise-ro-crate-profile/dev

## Tooling

The following tools are used to generate, validate, or modify the profile.

### Environment Setup

1. Create the virtual environment:

    ```bash
    bash utils/create-venv.sh
    ```

    This creates `venv-rise-profile/` in the repository root and installs dependencies from `requirements.txt`.

2. Activate the virtual environment:

    ```bash
    source venv-rise-profile/bin/activate
    ```

3. Generate the profile:

    ```bash
    python generate_profile.py
    ```

### Profile Generation

The profile is defined in `profile_definition.json`. The script `generate_profile.py` generates all profile resources from it:

- `rise-ro-crate-profile.md` — Profile description page
- `ro-crate-metadata.json` — Profile Crate
- `types.csv` / `vocabulary.csv` — External type mappings and profile vocabulary
- `context.jsonld` — JSON-LD context
- `rise-ro-crate-profile-schema.json` — JSON Schema for validation
- `rise-ro-crate-profile.ts` — TypeScript interfaces
- `rise_ro_crate_profile_pydantic.py` — Pydantic models

All output files are written to the folder `generated_profile/`.

The Pydantic models can be installed with pip as the module `rise_ro_crate_profile_pydantic`.
Pin a commit, for example `pip install "rise-ro-crate-profile @ git+https://github.com/tumi8/rise-ro-crate-profile.git@<commit>"`.

### Profile Validation

The script `validate_metadata.py` validates if a `ro-crate-metadata.json` file conforms to the RISE profile.

```bash
python validate_metadata.py path/to/ro-crate-metadata.json
```

> **Note:** This validator is a work in progress. The main validation logic is functional, but not every edge case may be covered yet.

### Utility Scripts

| Script | Description |
|---|---|
| `utils/create-venv.sh` | Creates and initializes the virtual environment |
| `utils/build_pages.sh` | Builds versioned profile pages from git tags (used by CI) |
| `utils/build_structure_svg.sh` | Compiles the structure diagram from LaTeX to SVG |

## Disclaimer

The tooling scripts (`generate_profile.py`, `validate_metadata.py`, utility scripts) were created with the help of AI coding tools.
The profile design and definitions are human-authored.
