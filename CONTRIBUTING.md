# Contributing to Multi-Agent Defense Simulation

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Rust (latest stable)
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/multiagent-defense.git
   cd multiagent-defense
   ```

2. **Set up development environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Build the Rust library**
   ```bash
   cd interception_core
   maturin develop
   cd ..
   ```

4. **Run tests to verify setup**
   ```bash
   # Rust tests
   cd interception_core && cargo test && cd ..
   
   # Python integration tests
   python test_system_validation.py
   ```

## 🛠️ Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow existing code style and conventions
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run all tests
   cd interception_core && cargo test && cd ..
   python test_system_validation.py
   python test_pathfinding.py
   
   # Test simulation
   python simulation/run_simulation.py
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Brief description of changes"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure all tests pass

### Code Style Guidelines

#### Rust Code
- Follow standard Rust conventions (`cargo fmt`)
- Use `cargo clippy` to catch common issues
- Add documentation comments (`///`) for public APIs
- Write unit tests for new functions

#### Python Code
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings for classes and functions
- Keep line length under 100 characters

#### Documentation
- Use clear, concise language
- Include code examples where helpful
- Update README.md for significant changes
- Add GIF demonstrations for new scenarios

## 🎯 Areas for Contribution

### Core Algorithm Improvements
- **Multi-intruder scenarios** - Support for multiple coordinated intruders
- **Dynamic obstacles** - Environmental obstacles that change over time
- **Communication constraints** - Limited communication between defenders
- **3D simulation** - Extension to three-dimensional environments

### Performance Optimizations
- **GPU acceleration** - CUDA/OpenCL for large-scale simulations
- **Parallel processing** - Multi-threaded defender calculations
- **Memory optimization** - Reduced memory footprint for long simulations

### Visualization Enhancements
- **Interactive controls** - Real-time parameter adjustment
- **3D visualization** - Three-dimensional scene rendering
- **Performance metrics** - Real-time statistics and analytics
- **Export formats** - Additional output formats (MP4, SVG)

### Testing and Quality
- **Benchmark tests** - Performance regression testing
- **Fuzzing** - Robustness testing with random inputs
- **Integration tests** - More comprehensive scenario testing
- **Documentation** - API documentation and tutorials

## 🐛 Bug Reports

When reporting bugs, please include:

- **Environment details** (OS, Python version, Rust version)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error messages** or logs
- **Minimal code example** if possible

Use the GitHub issue template and include relevant labels.

## 💡 Feature Requests

For new features:

- **Check existing issues** to avoid duplicates
- **Provide clear use case** and motivation
- **Consider implementation complexity**
- **Discuss breaking changes** if applicable

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts

### PR Description Should Include
- **Summary** of changes made
- **Motivation** for the changes
- **Testing** performed
- **Breaking changes** (if any)
- **Related issues** (link with `#issue-number`)

### Review Process
1. **Automated checks** must pass (CI/CD)
2. **Code review** by maintainers
3. **Testing** on multiple platforms
4. **Documentation review** if applicable
5. **Merge** after approval

## 🔒 Security

For security-related issues:
- **Do not** open public GitHub issues
- **Email** security concerns to the maintainers
- **Provide** detailed information about the vulnerability
- **Allow** reasonable time for fix before disclosure

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙋 Questions?

- **GitHub Discussions** for general questions
- **GitHub Issues** for bugs and feature requests
- **Code review comments** for implementation details

Thank you for contributing to Multi-Agent Defense Simulation! 🚀