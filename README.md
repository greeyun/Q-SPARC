# {YOUR-PROJECT-NAME}

{SHORT PROJECT DESCRIPTION}

![Python 3](https://img.shields.io/badge/Python->=3.9-blue)
[![Contributors][contributors-shield]][contributors-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![GitHub issues-closed][issues-closed-shield]][issues-url]
[![License][license-shield]][license-url]
[![Contributor Covenant][code-of-conduct-shield]](CODE_OF_CONDUCT.md)
[![PyPI version fury.io][pypi-shield]][pypi-url]
[![Conventional Commits][conventional-commits-shield]][conventional-commits-url]

[contributors-shield]: https://img.shields.io/github/contributors/{GITHUB_ACCOUNT}/{REPO_NAME}.svg?style=flat-square
[contributors-url]: https://github.com/{GITHUB_ACCOUNT}/{REPO_NAME}/graphs/contributors
[stars-shield]: https://img.shields.io/github/stars/{GITHUB_ACCOUNT}/{REPO_NAME}.svg?style=flat-square
[stars-url]: https://github.com/{GITHUB_ACCOUNT}/{REPO_NAME}/stargazers
[issues-shield]: https://img.shields.io/github/issues/{GITHUB_ACCOUNT}/{REPO_NAME}.svg?style=flat-square
[issues-url]: https://github.com/{GITHUB_ACCOUNT}/{REPO_NAME}/issues
[issues-closed-shield]: https://img.shields.io/github/issues-closed/{GITHUB_ACCOUNT}/{REPO_NAME}.svg
[issues-closed-url]: https://GitHub.com/SPARC-FAIR-Codeathon/sparc-me/issues?q=is%3Aissue+is%3Aclosed
[license-shield]: https://img.shields.io/github/license/{GITHUB_ACCOUNT}/{REPO_NAME}.svg?style=flat-square
[license-url]: https://github.com/{GITHUB_ACCOUNT}/{REPO_NAME}/blob/master/LICENSE
[code-of-conduct-shield]: https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg
[pypi-shield]: https://badge.fury.io/py/{PYPI_PROJECT_NAME}.svg
[pypi-url]: https://pypi.python.org/pypi/{PYPI_PROJECT_NAME}}/
[conventional-commits-shield]: https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white
[conventional-commits-url]: https://conventionalcommits.org


## HOW TO USE THIS TEMPLATE

Please read [ABOUT_THIS_TEMPLATE](ABOUT_THIS_TEMPLATE.md), and delete this section.


## Table of contents
* [About](#about)
* [Getting started](#getting-started)
* [Contributing](#contributing)
* [Reporting issues](#reporting-issues)
* [Contributors](#contributors)
* [Acknowledgements](#acknowledgements)


## About

This is the repository of team **TBC** (Team G) of the 2025 SPARC Codeathon. Information about the 2025 SPARC Codeathon can be found [here](https://sparc.science/news-and-events/events/2025-sparc-fair-codeathon).

No work was done on this project prior to the Codeathon.

## Introduction

The NIH Common Fund's Stimulating Peripheral Activity to Relieve Conditions (SPARC) program aims to advance our understanding of how electrical signals regulate internal organ function. By investigating these mechanisms, SPARC explores the potential for therapeutic devices to modulate nerve activity as treatments for conditions such as hypertension, heart failure, and gastrointestinal disorders. This comprehensive research initiative has aggregated data from over 60 research groups, encompassing more than 3,900 subjects across 8 species and 49 different anatomical structures.

The SCKAN Natural Language Interface (SCKAN NLI, http://fdi-nlp.ucsd.edu/) is an AI-based query interface customized for retrieving high-level connectivity knowledge from SCKAN. The NLI leverages the GPT-4o mini ("o" for "omni") model to extract contextual semantic frames related to SCKAN's connectivity knowledge and generates answers using natural language expressions. The technical overview of the SCKAN NLI can be found [here](https://github.com/smtifahim/SCKAN-Apps/blob/master/sckan-explorer/json/sckan-nli/technical-overview.md).

## The Problem

Large language models (LLMs) have revolutionized how users interact with complex scientific databases, offering the potential for intuitive, natural language queries that democratise access to specialised knowledge. However, the current SCKAN NLI implementation falls short of delivering an optimal user experience that could significantly enhance engagement with the broader SPARC Platform.

While the SCKAN NLI provides valuable functionality, several critical limitations prevent it from fully leveraging the power of modern LLMs and restrict user adoption across the SPARC ecosystem:

1. **Response Time**: This is an experimental service that relies on GPT-4. The response time for the SCKAN NLI is primarily (>95%) dictated by GPT-4's own response times.

2. **Lack of Conversational Memory & Limited Interactive Chatbot Functionality**: The chatbot cannot remember previous questions and functions more as a query tool than an interactive chatbot. This means users must phrase their entire query in a single turn, which makes the bot seem unintelligent. For example, if you ask it about the previous question, the SCKAN-NLI will give an unrelated answer. It is essentially a single-turn Q&A system rather than a conversational interface.

3. **Redundant Architecture**: The use of multiple API calls and multiple LLM calls makes the overall logic overly redundant and complex.

4. **Inability to Integrate Flatmap**: The system cannot be integrated with Flatmap.

5. **User Interface Limitations**: Doesn't include chat history.

These limitations create friction that discourages researchers from fully exploring SCKAN's rich connectivity data, ultimately reducing the scientific impact and utility of the entire SPARC

## Our Solution 

1. **Local Server**
2. **History Memory**



### Pre-requisites 
- Python versions:
   - 3.9
###  Installing via PyPI

Here is the [link](https://pypi.org/project/{PACKAGE_NAME}/) to our project on PyPI
```
pip install {PACKAGE_NAME}
```

## Contributing

See [Contributing](CONTRIBUTING.md)

## Reporting issues 
To report an issue or suggest a new feature, please use the [issues page](https://github.com/GITHUB_ACCOUNT/{REPO_NAME}/issues). 
Please check existing issues before submitting a new one.

## Contributors

## Acknowledgements 


## References: 
[1] SCKAN NLI Technical Overview. https://github.com/smtifahim/SCKAN-Apps/blob/master/sckan-explorer/json/sckan-nli/technical-overview.md
