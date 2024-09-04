## Contributing Guidelines
<hr>

Thank you for considering contributing to our project! We welcome contributions from everyone. To maintain a positive and collaborative environment, please follow these guidelines:

### Creating Issues:
<hr>

1. **Search Existing Issues**: Before creating a new issue, please search existing issues to see if the topic has already been discussed or reported.

2. **Clear and Descriptive Title**: Provide a clear and descriptive title for your issue, summarizing the problem or enhancement.

3. **Detailed Description**: Provide a detailed description of the issue, including steps to reproduce (if applicable), expected behavior, and actual behavior.

4. **Use Labels**: Use appropriate labels to categorize your issue (e.g., bug, enhancement, documentation, etc.).

### Development Setup:
<hr>

1. Fork and clone the Repository
2. Pull latest changes from the main repository if it has diverged
3. Add Rye on your system if it is not installed already. [Source](https://rye-up.com/guide/installation/)
4. Install all the dependencies using `rye sync`.
5. Install pre-commit hook using `rye run pre-commit install`
6. Run `rye add package_name` (if you wish to add any packages as per your requirements.) and make sure to execute ```rye sync``` to add these dependencies in your working environment.
7. Run tests using `rye run pytest` or `rye run pytest -k test_function_name -v` to run specific file.
8. Do not push changes without the tests and coverage passing
9. Commit your changes with **proper** commit messages in imperative form like `Add my best feature`, `Fix issues causing whatever`, `Update docs` etc: [Good reference here](https://cbea.ms/git-commit/)
10. Make changes and push to your forked repository
11. Create PR to the forked repository as mentioned below


### Pull Requests (PRs):
<hr>

1. **Fork the Repository**: Start by forking the repository to your GitHub account.

2. **Clone the Repository**: Clone the forked repository to your local machine using the `git clone` command.

3. **Create a Branch**: Create a new branch for your contribution. Use descriptive and concise names for your branches. Avoid using special characters and whitespace.

4. **Make Changes**: Make your desired changes to the codebase.

5. **Code Style:** Follow the existing code style and conventions. Ensure proper indentation, variable naming, and commenting.

5. **Test Your Changes**: Ensure that your changes do not break existing functionality. Write test cases to cover your code changes. Ensure that existing tests pass successfully.

6. **Commit Your Changes**: Commit your changes. Write clear and meaningful commit messages. Include a brief summary in the first line followed by a more detailed description if necessary.

7. **Push Changes**: Push your changes to your forked repository.

8. **Submit a Pull Request (PR)**: Once you have pushed your changes, submit a pull request to the main repository. Use a descriptive title for your pull request that summarizes the changes made.

9. **Review Process**: Your PR will be reviewed by project maintainers. Please be patient during the review process and be open to feedback and suggestions.

10. **Merge PR**: If your PR is approved, it will be merged into the main repository. Congratulations on your contribution!

11. **Stay Engaged**: Stay engaged with the community, participate in discussions, and consider contributing further.

Thank you for your interest in contributing to our project! Your contributions help make this project better for everyone.