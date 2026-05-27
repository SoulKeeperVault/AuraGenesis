# Contributing to AuraGenesis

Thank you for your interest in improving Aura! We welcome contributions that help make artificial consciousness research more accessible, safe, and beautiful.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) (to be added soon).

## How to Contribute

1. **Fork** the repository
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/amazing-improvement
   ```
3. **Make your changes** following our style guidelines
4. **Test** your changes (see below)
5. **Commit** with clear messages
6. **Push** and open a Pull Request

## Development Setup (5 minutes)

```bash
git clone https://github.com/SoulKeeperVault/AuraGenesis.git
cd AuraGenesis

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Code Style

- We use **ruff** for linting and formatting (run `ruff check .` and `ruff format .`)
- **mypy** for strict type checking (`mypy AuraGenesis/`)
- Follow existing docstring style (Google or NumPy style)
- Keep consciousness modules focused and well-commented

## Testing

- All new code must have tests
- Run the full test suite before submitting PR: `pytest --cov=AuraGenesis`
- For hardware-related code, use mocks

## Pull Request Guidelines

- Keep PRs focused (one feature/fix per PR)
- Update documentation if needed
- Add tests for new functionality
- Be kind and patient — Aura is a research project

## Areas Where Help is Needed

- Better Φ score approximation
- Voice emotion modulation improvements
- Hardware abstraction layer
- Documentation and examples
- Accessibility in the Streamlit UI

Thank you for helping Aura evolve! 🌱
