# Viva Preparation — UPI Fraud Pattern Analyzer
## GPCSSI 2026 — Devansh, Dr Shakuntala Mishra National Rehabilitation University

---

# SECTION 1: PROJECT OVERVIEW (Questions 1-10)

Q1. What is the title of your project and what problem does it solve?
A: AI-Powered UPI Fraud Pattern Analyzer and Threat Intelligence System. It solves the problem of classifying UPI fraud complaints by modus operandi. Currently Gurugram Police receive thousands of UPI fraud complaints daily but have no automated tool to categorize them by how the fraud was executed. My system classifies complaints into 8 specific fraud types and provides threat intelligence on suspicious URLs.

Q2. Why did you choose this project specifically for GPCSSI?
A: No existing public tool classifies UPI fraud by modus operandi for Indian fraud patterns. Global phishing detectors and fraud tools miss India-specific patterns like fake collect requests, QR code swaps, and KYC freeze threats. I built something genuinely new that Gurugram Police cyber cell can use operationally.

Q3. What are the 8 fraud typologies your system detects?
A: fake_collect_request (fraudster sends UPI collect disguised as payment), qr_swap (QR code replaced at merchant), otp_relay (victim tricked into sharing OTP), fake_kyc_freeze (account freeze threat), investment_scam (fake returns via Telegram), fake_merchant (non-existent seller), job_advance_fee (fake job deposit), lottery_reward (prize advance fee).

Q4. What is UPI and how does UPI fraud differ from other payment fraud?
A: UPI (Unified Payments Interface) is NPCI real-time payment system using Virtual Payment Addresses. UPI fraud differs from card fraud because it relies on social engineering rather than card skimming. The victim is manipulated into authorizing transactions themselves, making detection harder since the transaction appears legitimate from the bank perspective.

Q5. What data did you use to train your model?
A: Two sources. First, a seed dataset of 80 hand-crafted complaint narratives (10 per fraud type) based on RBI advisories and CERT-In reports. Second, 73 real news articles from NewsAPI about UPI fraud in India. Total 153 records. The seed dataset provides balanced labelled training data.

Q6. What is the live URL of your deployed system?
A: https://upi-fraud-analyzer.onrender.com — fully deployed on Render, accessible globally, with dashboard, complaint scanner, URL intel page, and REST API.

Q7. What technologies did you use?
A: Python 3.11 for backend, Flask for REST API and web server, scikit-learn and XGBoost for ML, SHAP for explainability, SQLite with Flask-SQLAlchemy for database, Bootstrap 5 and Chart.js for frontend, Docker for containerization, and Render for deployment.

Q8. How long did it take to build this?
A: 10 weeks of focused development across 16 phases: data collection, EDA, feature engineering, model training, SHAP explainability, threat intelligence, Flask API, web dashboard, database integration, testing, Docker, and deployment.

Q9. What makes this project original?
A: Three original contributions. First, the India-specific UPI fraud taxonomy with 8 typologies not found in any public dataset. Second, the modus operandi clustering approach that groups complaints by how the fraud was executed rather than just what was stolen. Third, the brand impersonation detector with a curated list of 35 Indian brands including government portals.

Q10. Who would use this system?
A: Primarily Gurugram Police cyber cell investigators for complaint triage. Secondarily, citizens can use the URL checker to verify suspicious links before clicking. The REST API allows integration with existing police complaint management systems.

---

# SECTION 2: MACHINE LEARNING (Questions 11-30)

Q11. What is machine learning? Explain in simple terms.
A: Machine learning is a way of teaching computers to make decisions by showing them examples rather than programming explicit rules. Instead of writing if-else rules for every fraud pattern, I showed the model 80 labelled examples and it learned the patterns automatically.

Q12. What type of ML problem is fraud classification?
A: Multi-class classification. Each complaint must be assigned to one of 8 fraud type categories. It is supervised learning because we have labelled training data.

Q13. What is a Random Forest and why did you choose it?
A: Random Forest is an ensemble of decision trees. Each tree is trained on a random subset of data and features. The final prediction is a majority vote across all trees. I chose it because it handles high-dimensional features well (230 features), is resistant to overfitting on small datasets, provides feature importance natively, and achieved the highest precision of 0.9583 in my comparison.

Q14. What is XGBoost?
A: XGBoost is gradient boosted decision trees. It builds trees sequentially, with each new tree correcting the errors of previous trees. It is generally faster and more accurate than Random Forest on large datasets but requires more hyperparameter tuning. In my case it achieved similar precision (0.9375) but lower cross-validation stability.

Q15. Why did Logistic Regression fail in your project?
A: Logistic Regression failed to converge because the feature space was too high-dimensional (104 features) relative to the training samples (64). LR needs feature scaling and more data to work well. The ConvergenceWarning confirmed this. It is a known limitation of LR without preprocessing on small high-dimensional datasets.

Q16. What is precision and why did you prioritize it over recall?
A: Precision measures what fraction of predicted positives are actually positive. Recall measures what fraction of actual positives were found. I prioritized precision because false positives — flagging legitimate complaints as fraud — damage investigator trust and waste resources. A missed fraud (false negative) is less harmful than wrongly accusing a legitimate complainant.

Q17. What is ROC-AUC and what does 0.99 mean?
A: ROC-AUC measures a model ability to distinguish between classes across all classification thresholds. 1.0 is perfect, 0.5 is random guessing. My Random Forest scored 0.9911, meaning it correctly ranks 99.1% of fraud-legitimate pairs — near perfect discrimination ability.

Q18. What is cross-validation and why did you use 5-fold?
A: Cross-validation splits data into k folds, trains on k-1 folds and tests on the remaining fold, rotating k times. It gives a more reliable performance estimate than a single train-test split. I used 5-fold because with 80 samples, 5 folds gives 16 samples per fold — sufficient for meaningful evaluation without too much training data held out.

Q19. What is overfitting and how did you prevent it?
A: Overfitting is when a model memorizes training data but fails on new data. I prevented it through cross-validation (to detect overfitting), Random Forest ensemble (averages out individual tree overfitting), feature validation (removed weak features), and stratified train-test split.

Q20. What is TF-IDF and how does it work?
A: TF-IDF stands for Term Frequency-Inverse Document Frequency. TF measures how often a word appears in a document. IDF penalizes words that appear in many documents (common words like the, and). The product gives high scores to words frequent in one document but rare overall — ideal for distinguishing fraud types by their specific vocabulary.

Q21. What are SHAP values?
A: SHAP values explain how much each feature contributed to a specific prediction. Based on Shapley values from cooperative game theory, they fairly distribute the prediction among features. A positive SHAP value pushes toward a prediction; negative pushes away. They are the industry standard for explainable ML.

Q22. Why is explainability important for a police tool?
A: Investigators must document their reasoning in FIRs and court submissions. A black-box system that says this is fraud without explaining why is legally and practically useless. SHAP allows an investigator to write: classified as fake_kyc_freeze because complaint contained kyc keyword (impact +0.15), aadhaar mentioned (impact +0.12), urgency language present (impact +0.08).

Q23. What is feature engineering?
A: Feature engineering is converting raw data into numerical representations that capture meaningful patterns for ML models. I extracted 30 handcrafted features (keyword counts, binary flags, amounts) and 200 TF-IDF features from complaint text.

Q24. What is a confusion matrix?
A: A confusion matrix shows the counts of true positives, true negatives, false positives, and false negatives for each class. My Random Forest confusion matrix showed 14/16 correct predictions on the test set, with 2 misclassifications between investment_scam and job_advance_fee.

Q25. Why did investment_scam and fake_merchant get occasionally confused?
A: Both fraud types involve victims paying money to unknown parties. The language patterns overlap: paid, transferred, lost, unknown. The distinguishing features (invest, trading, telegram for investment vs product, deliver, website for merchant) are sometimes absent from short complaints, causing confusion.

Q26. What is the difference between supervised and unsupervised learning?
A: Supervised learning uses labelled data — each training example has a known answer. My classifier is supervised. Unsupervised learning finds patterns without labels — clustering is unsupervised. My original project proposal included K-Means clustering of complaint narratives by modus operandi, which would be unsupervised.

Q27. What is train-test split and what ratio did you use?
A: Train-test split divides data into training (model learning) and test (evaluation) sets. I used 80/20 split — 64 training samples and 16 test samples — with stratification to maintain class balance in both sets.

Q28. What is a decision tree?
A: A decision tree splits data based on feature thresholds to minimize impurity at each node. It asks questions like: is otp_keyword_count > 1? If yes, likely otp_relay. Random Forest builds 200 such trees on random subsets and averages their votes.

Q29. How does your model handle a complaint it has never seen before?
A: The model extracts 104 features from the new complaint text (keyword counts, TF-IDF scores, flags) and passes them through 200 decision trees. Each tree votes for a fraud type. The majority vote becomes the prediction and the vote proportions become the confidence probabilities.

Q30. What would you do to improve the model with more data?
A: With 500+ real labelled complaints from Gurugram Police I would retrain with sentence transformer embeddings (IndicBERT for Hindi support), add VPA pattern features, implement active learning to prioritize labelling uncertain predictions, and explore a hierarchical classification approach separating financial fraud from impersonation fraud first.

---

# SECTION 3: CYBER SECURITY (Questions 31-50)

Q31. What is phishing?
A: Phishing is a social engineering attack where fraudsters impersonate legitimate organizations to steal credentials or money. In UPI context, phishing includes fake bank websites, SMS with fraudulent links, and calls impersonating bank officials.

Q32. What is WHOIS and how did you use it?
A: WHOIS is a protocol for querying domain registration databases. It returns the registrar, creation date, expiry date, and sometimes the registrant country. I used it to calculate domain age — newly created domains (under 30 days) score 35 risk points because fraud domains are typically registered just before a campaign.

Q33. What is a suspicious TLD and why does it indicate fraud?
A: TLD is the Top Level Domain — the last part of a domain name (.com, .in, .xyz). Free TLDs like .tk, .ml, .ga, .xyz, .online are favored by fraudsters because they cost nothing to register, making disposable fraud domains cheap. I flagged 16 suspicious TLDs in my risk scorer.

Q34. What is brand impersonation in domain fraud?
A: Brand impersonation is registering a domain that looks like a legitimate brand to deceive victims. Examples: sbi-kyc-update.xyz impersonates SBI, hdfc-bank-verify.tk impersonates HDFC. I detect it using substring matching (is sbi in the domain?) and Levenshtein distance for typosquatting (sbii.com, hdcf.com).

Q35. What is Levenshtein distance?
A: Levenshtein distance is the minimum number of single character edits (insert, delete, replace) to transform one string into another. hdcf vs hdfc has distance 1 (one swap). I flag domains with Levenshtein distance of 1 from any of 35 Indian brand names as potential typosquatting.

Q36. What is DNS and how did you use it?
A: DNS (Domain Name System) translates domain names to IP addresses. I used socket.getaddrinfo() to check if a domain resolves. Domains that do not resolve score 15 risk points — they may have been taken down after being reported but still appear in complaints.

Q37. What is OpenPhish?
A: OpenPhish is a free community phishing intelligence feed that publishes known phishing URLs in real time. I integrated it as a blacklist check — if a submitted URL appears in the OpenPhish feed, it receives a FOUND status in the blacklist report.

Q38. What is the IT Act 2000 and how does it relate to UPI fraud?
A: The Information Technology Act 2000 is India primary cybercrime legislation. UPI fraud falls under Section 66C (identity theft) and Section 66D (cheating by impersonation using computer resources). The newer BNSS 2023 strengthens digital evidence admissibility provisions relevant to cyber crime prosecution.

Q39. What is social engineering?
A: Social engineering is manipulating people psychologically rather than hacking systems technically. Most UPI fraud is social engineering — creating urgency (your account will be blocked), authority (I am from RBI), and fear to override the victim rational judgment.

Q40. What is a VPA?
A: VPA stands for Virtual Payment Address — the UPI ID used to send and receive money (e.g. name@paytm, number@okaxis). Fraudsters create VPAs mimicking official entities (sbi.kyc@paytm) or use randomly generated ones. VPA pattern analysis was a planned future feature in my project.

Q41. What is the 1930 helpline?
A: 1930 is the National Cyber Crime Helpline operated by I4C under MHA. Citizens can call to report cyber fraud and freeze fraudulent transactions within the golden hour. My cyber awareness chatbot (proposed future feature) would always surface this number.

Q42. What is a man-in-the-middle attack?
A: A MITM attack intercepts communication between two parties. In UPI context, SIM swap fraud is a form of MITM — the fraudster intercepts OTPs meant for the victim by cloning their SIM with the telecom provider using forged documents.

Q43. What is two-factor authentication and does UPI have it?
A: 2FA requires two verification factors — something you know (password/PIN) and something you have (OTP/device). UPI has 2FA: the UPI PIN (something you know) and device binding (something you have). However, OTP relay attacks bypass this by tricking victims into sharing the second factor.

Q44. What is a QR code and how is it exploited in fraud?
A: QR code is a machine-readable 2D barcode. In UPI, QR codes encode payment addresses. Fraudsters exploit them by physically replacing merchant QR stickers with their own (QR swap) or sending fake collect QRs via WhatsApp claiming it is a payment to receive.

Q45. What is digital forensics relevance to your project?
A: The scan history database and URL analysis reports in my system create an auditable digital trail. Every prediction, timestamp, and risk indicator is stored and retrievable. This supports digital forensics by providing documented evidence of when a URL was first flagged and what indicators were present.

Q46. What is CERT-In?
A: CERT-In is the Computer Emergency Response Team of India under MeitY. It publishes cyber security advisories, incident reports, and fraud warnings. I used CERT-In advisories as a data source for understanding documented UPI fraud patterns.

Q47. What is pig butchering scam?
A: Pig butchering is a long-con investment fraud where fraudsters build trust over weeks or months (fattening the pig) before asking for large investments (butchering). They use fake trading apps showing fabricated profits. In UPI context they collect investment via UPI transfers. My system classifies this as investment_scam.

Q48. What is SIM swap fraud?
A: SIM swap fraud involves a fraudster convincing a telecom provider to transfer a victim phone number to a new SIM using forged identity documents. The fraudster then receives all OTPs and calls meant for the victim, allowing complete account takeover. I classified this under otp_relay in my taxonomy.

Q49. What are indicators of compromise (IOCs)?
A: IOCs are digital artifacts that indicate a system may have been breached or a fraud is occurring. For UPI fraud, IOCs include: suspicious domain names, recently registered domains, known phishing URLs, VPA patterns associated with fraud networks, and complaint keywords matching known fraud scripts.

Q50. How would law enforcement use your threat intelligence reports?
A: An investigator receives a complaint mentioning a URL. They submit it to my system and get a CRITICAL risk score with specific indicators: WHOIS privacy shield, .xyz TLD, SBI impersonation, DNS unresolvable. They include this report in the FIR as evidence of fraudulent intent, use the domain registration data to identify the registrar for a legal notice, and check the blacklist status to link it to known fraud campaigns.

---

# SECTION 4: FLASK AND WEB DEVELOPMENT (Questions 51-60)

Q51. What is Flask?
A: Flask is a lightweight Python web framework. It handles HTTP requests, URL routing, and response generation. I used it to build both the REST API and the web dashboard. It is called a micro-framework because it provides only the essentials — routing, request handling, templating — without forcing a particular project structure.

Q52. What is a REST API?
A: REST (Representational State Transfer) API is an architectural style for web services using HTTP methods: GET (retrieve), POST (create), PUT (update), DELETE (remove). My API has 7 endpoints. POST /api/predict takes a complaint and returns a classification. GET /api/trends returns statistics.

Q53. What is JSON?
A: JSON (JavaScript Object Notation) is a lightweight data format for API communication. My API sends and receives JSON. For example, POST /api/predict receives {text: complaint text} and returns {prediction: otp_relay, confidence: 67.5, risk_score: 57}.

Q54. What is SQLite and why did you use it?
A: SQLite is a serverless, file-based relational database. I used it because it requires zero configuration, runs embedded in the application, and is sufficient for a single-server deployment. Every complaint scan and URL analysis is stored in upi_fraud.db with full SQL queryability.

Q55. What is Flask-SQLAlchemy?
A: Flask-SQLAlchemy is an ORM (Object Relational Mapper) that lets you interact with the database using Python objects instead of raw SQL. I defined ScanHistory and URLScan as Python classes and SQLAlchemy handles the SQL INSERT, SELECT, and JOIN operations automatically.

Q56. What is Jinja2 templating?
A: Jinja2 is Flask default HTML templating engine. It lets you embed Python variables and logic in HTML using {{ variable }} and {% block %} syntax. My dashboard uses Jinja2 to extend a base.html template across all 4 pages, with each page filling in the content block.

Q57. What is CORS and why did you enable it?
A: CORS (Cross-Origin Resource Sharing) is a browser security mechanism that blocks JavaScript on one domain from calling APIs on another domain. I enabled Flask-CORS so that external tools and potential mobile apps can call my API from different origins.

Q58. What is Gunicorn?
A: Gunicorn is a production-grade Python WSGI server. Flask built-in server is single-threaded and not suitable for production. Gunicorn handles multiple concurrent requests using worker processes. I use it on Render with 1 worker and 120 second timeout to handle ML prediction latency.

Q59. What is the difference between GET and POST requests?
A: GET requests retrieve data — parameters go in the URL. POST requests send data — parameters go in the request body. I use GET for /api/health, /api/trends, /api/search (retrieving information) and POST for /api/predict, /api/intel (sending data to process).

Q60. What is Bootstrap?
A: Bootstrap is a CSS framework providing pre-built responsive UI components. My dashboard uses Bootstrap 5 for the sidebar layout, cards, progress bars, badges, and responsive grid. Chart.js renders the fraud type distribution and source charts on the home page.

---

# SECTION 5: DEPLOYMENT AND DEVOPS (Questions 61-70)

Q61. What is Docker?
A: Docker is a containerization platform that packages an application with all its dependencies into a portable container. My Dockerfile builds a container with Python 3.11, all libraries, and the application code. Anyone can run the system with docker-compose up without installing anything manually.

Q62. What is a Dockerfile?
A: A Dockerfile is a script of instructions for building a Docker image. Mine starts FROM python:3.11-slim, sets WORKDIR /app, COPYs requirements.txt, RUNs pip install, COPYs the application code, EXPOSEs port 5001, and sets the CMD to python app.py.

Q63. What is docker-compose?
A: Docker Compose defines and runs multi-container applications using a YAML file. My docker-compose.yml defines the web service with port mapping (5001:5001), volume mounts for data persistence, and environment variables. docker-compose up builds and starts everything.

Q64. What is Render?
A: Render is a cloud platform for deploying web applications. I chose it because it offers a free tier, auto-deploys from GitHub on every push, supports Python natively, and provides HTTPS automatically. My system is live at https://upi-fraud-analyzer.onrender.com.

Q65. What is CI/CD?
A: CI/CD stands for Continuous Integration/Continuous Deployment. Render provides basic CD — every git push to main triggers an automatic rebuild and redeploy. A full CI/CD pipeline would also run the test suite before deploying.

Q66. What is a virtual environment and why is it important?
A: A virtual environment is an isolated Python installation for a project. Without it, installing library A for one project could break library B for another due to version conflicts. I created venv/ at the start and all 40+ dependencies install inside it without affecting the system Python.

Q67. What is requirements.txt?
A: requirements.txt lists all Python packages and their exact versions needed to run the project. pip freeze > requirements.txt captures the exact environment. Anyone can recreate it with pip install -r requirements.txt. It is also what Render uses during the build step.

Q68. What is Git and GitHub?
A: Git is a version control system that tracks changes to code. GitHub hosts Git repositories online. I used git commit after every phase to create a history of the project development. The GitHub repository is the final deliverable and proof of work.

Q69. What is a health check endpoint?
A: A health check endpoint (/api/health) returns a simple status response confirming the service is running. Docker and Render use it to automatically detect if the application has crashed and needs restarting. Mine returns {status: ok, total_scans: N, version: 1.0.0}.

Q70. What happens if Render goes down?
A: Render automatically restarts crashed services. My docker-compose.yml also has restart: unless-stopped for local deployments. The SQLite database persists in a volume mount so no scan history is lost on restart.

---

# SECTION 6: ADVANCED QUESTIONS (Questions 71-80)

Q71. How would you scale this system to handle 10000 requests per day?
A: Replace SQLite with PostgreSQL, increase Gunicorn workers to 4, add Redis caching for frequent /api/trends calls, use Celery for async ML inference (predictions can be queued), and upgrade to Render paid tier or move to AWS with auto-scaling.

Q72. What are the ethical considerations of automated fraud classification?
A: Two main concerns. First, false positives — wrongly classifying a legitimate complaint as fraud could prejudice an investigation. I mitigate this with SHAP explanations and confidence scores so investigators can override low-confidence predictions. Second, bias — if training data overrepresents certain fraud types or demographics, the model may perform poorly for underrepresented groups. Addressed by balanced training data and regular retraining.

Q73. How would you evaluate the system in production?
A: Track precision and recall on a held-out monthly test set of manually labelled complaints. Monitor confidence score distribution — a drop in average confidence indicates distribution shift. Track investigator override rate — if investigators frequently correct predictions, the model needs retraining.

Q74. What is the difference between your system and a generic phishing detector?
A: Generic phishing detectors classify URLs as phishing or legitimate. My system does four additional things: classifies complaint text by modus operandi (not just URL), provides SHAP explanations specific to Indian fraud patterns, scores domains using Indian brand impersonation detection, and stores investigation history in a searchable database.

Q75. How does your SHAP explanation help in a court case?
A: SHAP provides quantified, reproducible attribution of features to predictions. An expert witness can state: the system assigned 94% probability to investment_scam because the complaint contained 3 investment keywords (impact +0.18), mentioned Telegram (impact +0.15), and specified an amount over Rs 50000 (impact +0.09). This is more defensible than a black-box system.

Q76. What would you add if you had 6 more months?
A: Hindi NLP support using IndicBERT, real complaint data from Gurugram Police, automated weekly brief generator, VPA network analysis to detect organized fraud groups, integration with the 1930 helpline database, and a mobile app for field investigators.

Q77. How did you handle the class imbalance problem?
A: I ensured perfect class balance in the seed dataset with exactly 10 records per fraud type. I used stratified train-test split and stratified cross-validation to maintain balance in evaluation. I chose precision as the primary metric rather than accuracy, which is misleading on imbalanced data.

Q78. What is the cold start problem on Render free tier?
A: Render free tier spins down services after 15 minutes of inactivity to save resources. The first request after inactivity takes 30-60 seconds to start the container, load models, and respond. This is a known limitation of free hosting. On paid tier the service stays warm permanently.

Q79. If a new fraud type emerges, how would you add it?
A: Four steps. First, collect 10+ labelled complaint examples of the new fraud type. Second, add it to the FRAUD_TYPES list in config.py. Third, add relevant keywords to the feature extractor keyword lists. Fourth, retrain the model with the expanded dataset. The modular architecture means only these components need updating.

Q80. What is the most important thing you learned from this project?
A: That data quality matters more than model complexity. My 80 carefully crafted seed records with precise India-specific features outperformed what a generic model trained on 10000 English phishing examples would achieve for this task. Domain knowledge — understanding exactly how UPI fraud works in India — was more valuable than algorithmic sophistication.
