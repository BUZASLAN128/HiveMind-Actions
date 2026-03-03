# Contributing to HiveMind Actions

Thanks for contributing.

## Contribution Flow (PR to `main`)

1. Fork the repository.
2. Clone your fork.
3. Create a feature branch.
4. Make focused changes.
5. Push your branch.
6. Open a Pull Request targeting `main`.

Example:

```bash
git checkout -b feature/amazing-feature
git add .
git commit -m "feat: add amazing feature"
git push origin feature/amazing-feature
```

## Minimal Validation Before PR

- Confirm workflow docs match implementation files in `.github/workflows/`.
- Validate links and section integrity in `README.md`.
- Run Python tests after dependencies are installed:

```bash
python -m pip install -r .github/requirements.txt
python -m pytest .github/scripts/test_ai_utils.py .github/scripts/test_analyzer.py -q
```

## AI Review Process

- Analyst/Coder/Reviewer workflows are part of the repository quality gate.
- Reviewer may request or trigger self-correction if quality criteria are not met.

## Ground Rules

- Follow `.github/swarm_rules.md`.
- Keep changes small, clear, and documented.
- Do not commit secrets or private credentials.

## Contact

For urgent security matters: **buzaslan.ea@gmail.com**

## License

By contributing, you agree that contributions are licensed under the MIT License.