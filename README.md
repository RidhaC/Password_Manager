## Project summary
The password manager project aims to create a secure and dependable application that helps people store and manage their login information safely. Weak, reused, or outdated passwords are still one of the main reasons data breaches occur, and many users struggle to keep track of multiple accounts across different platforms. While many password management tools exist, some lack features that promote strong password habits or sacrifice usability for security, which can discourage consistent use.

Our application takes a practical approach by combining strong encryption and authentication with tools that are easy to use. All stored credentials are protected using AES-256 encryption and secured behind a single master password, ensuring that sensitive information remains protected even if the local database is compromised. The system also includes features such as a password generator, password strength scoring, and alerts for reused or outdated passwords to help users maintain better security practices.

The application runs as a local desktop program, giving users full control over their data without requiring an internet connection. Throughout development, the project evolved based on technical constraints, testing results, and feedback, ultimately resulting in a more refined and realistic final system. The sections below describe the project’s background, key changes made during development, and the final scope of the completed application.

## Project Background and Initial Goals

At the start of the project, the primary goal was to design a password manager that balanced strong security with ease of use. The team wanted to create an application that users could trust with sensitive information while still feeling intuitive and accessible. Early discussions explored different deployment options, including browser-based solutions, but concerns related to security, complexity, and time constraints led the team toward a local desktop application instead.

The initial vision focused on protecting credentials through encryption and secure authentication while also encouraging better password habits. From the beginning, the project emphasized preventing common security issues such as password reuse and weak password selection. These goals guided early design decisions and shaped how features were prioritized throughout development.




## Project Evolution and Key Changes

As development progressed, the project went through several changes in response to testing, feedback, and a clearer understanding of implementation challenges. One of the most significant shifts was moving away from the original browser-based concept to a fully local application. This change allowed the team to focus more deeply on encryption, authentication, and offline security without the added complexity of browser APIs.

Another major evolution involved the user interface. Early versions of the application were functional but minimal, and as new features were added, the need for a more structured and modern interface became clear. Transitioning to a CustomTkinter-based interface improved navigation, consistency, and overall usability. Testing also became a stronger focus later in development, shifting attention beyond visual design to include database behavior, encryption validation, and error handling.

## Final System Scope and Capabilities

The final version of the password manager reflects the lessons learned and improvements made throughout the project. The application securely stores credentials using AES-256 encryption and protects access through a master password and multi-factor authentication. Users can add, edit, and manage credentials while receiving feedback on password strength, reuse, and age. A built-in password generator helps users create stronger passwords without manual effort.

In addition to security, usability was a key focus in the final system. The interface is designed to be clear and easy to navigate, allowing users to manage their credentials without confusion. By combining strong security practices with a user-friendly design, the completed password manager meets the functional and security requirements of the project and represents the final, stable version of the system delivered for this course.







## Required Python Packages & Installation Commands
**1. CustomTkinter:** Used for the modern GUI interface.

  **Install:** ```pip install customtkinter```.

**2. cryptography:** Used for AES encryption, hashing, and key generation.

  **Install:** ```pip install cryptography```.

**3. pyotp:** Used for TOTP-based Multi-Factor Authentication.

  **Install:** ```pip install pyotp```.

**4. qrcode:** Used to generate QR codes for MFA setup.

  **Install:** ```pip install qrcode```.

**7. image:** Required by some versions of qrcode for image processing.

  **Install:** ```pip install image```.

To install everything at once: ```pip install customtkinter cryptography pyotp qrcode image``` OR ```run pip install -r requirements.txt``` to run and install all packages from a dependency file

#
