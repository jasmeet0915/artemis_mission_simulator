# Contributing to Artemis Mission Simulator

Thanks for your interest in contributing! Here's how to get started.

## Getting Started

1. Browse open issues and add a comment to express your interest on working on any of them.
2. Fork the repository and clone your fork
3. Create a feature branch: `git checkout -b feature/label/my-change`. Here label can be name of the associated package or sub-system such as `scaffolding`, `docker`, `lunar_terrain_exporter`, etc.
4. Set up the development environment using Docker (see [README](README.md))

## Development Workflow

```bash
# Build and enter the container
./docker/build.sh
./docker/run.sh

# Build the workspace
colcon build --symlink-install
source install/setup.bash

# Run tests
colcon test
colcon test-result --verbose
```

## Pull Requests

1. Keep PRs focused — one feature or fix per PR
2. Add or update tests for any new functionality
3. Make sure all existing tests pass before submitting
4. Update documentation (READMEs, docstrings) if behaviour changes
5. Write clear commit messages describing *what* and *why*

## Code Style

- **Python:** Follow PEP 8. Use type hints for function signatures.
- **CMake/XML:** Match the formatting of surrounding code.
- **Commits:** Use a title in the beginning of the commit to specifying what the commit does. For instance, [fix], [feat], [refactor], etc. Use present tense, imperative mood (e.g. "Add terrain export" not "Added terrain export").

## Reporting Issues

Use [GitHub Issues](../../issues) with the provided templates. Include:
- Steps to reproduce
- Expected vs. actual behaviour
- Environment details (OS, Docker version, GPU)

## License

By contributing, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).
