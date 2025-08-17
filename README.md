# Lead Scoring MLOps

A production-ready, end-to-end MLOps platform for automated lead scoring, CRM integration, and real-time dashboarding. Built with Flask, scikit-learn, and a modular pipeline for fetching, preprocessing, training, prediction, monitoring, and alerting.

## 🚀 Features

- **Automated Lead Fetching**: Integrates with HubSpot CRM to fetch labeled/unlabeled leads.
- **Smart Data Merging**: [`src.training.smart_data_merger`](src/training/smart_data_merger.py) for deduplication and merging CRM with fresh API data.
- **Flexible Preprocessing**: [`src.preprocess.preprocess`](src/preprocess/preprocess.py) for feature engineering and data cleaning.
- **Model Training & Threshold Tuning**: Train, tune, and track models with [`src.train_model`](src/train_model.py) and [`src.tune_threshold`](src/tune_threshold.py).
- **Real-Time Prediction API**: Flask API in [`app/api.py`](app/api.py) with WebSocket dashboard updates.
- **Monitoring & Notification**: Model drift, performance, and alerting via [`src.monitor.monitor`](src/monitor/monitor.py) and [`src.monitor.notification`](src/monitor/notification.py).
- **MAB Model Selection**: Multi-armed bandit for model selection and traffic allocation.

## 📁 Project Structure

```
.
├── app/                # Flask API & dashboard routes
├── config/             # Configuration files (tokens, timestamps)
├── data/               # Data storage (raw, processed, adapted, predictions)
├── docs/               # Documentation
├── metadata/           # Model and training metadata
├── models/             # Saved models and preprocessors
├── src/                # Core ML, training, fetching, monitoring logic
├── requirements.txt    # Python dependencies
└── .env                # Environment variables
```

## ⚡️ Quickstart

1. **Install dependencies**
    ```sh
    pip install -r requirements.txt
    ```

2. **Set up environment variables**
    - Copy `.env.example` to `.env` and fill in your secrets (HubSpot, Flask, etc).

3. **Fetch CRM Data**
    ```sh
    python src/fetch/fetch_labled_leads.py
    python src/fetch/fetch_unlabled_leads.py
    ```

4. **Preprocess & Train**
    ```sh
    python src/training/train_baseline.py
    ```

5. **Run the API**
    ```sh
    python app/api.py
    ```

6. **Access Dashboard**
    - Open [http://localhost:5000](http://localhost:5000) for API docs and dashboard endpoints.

## 🧩 Key Modules

- **Data Fetching**: [`src.fetch.fetch_labled_leads`](src/fetch/fetch_labled_leads.py), [`src.fetch.fetch_unlabled_leads`](src/fetch/fetch_unlabled_leads.py)
- **Data Merging**: [`src.training.smart_data_merger`](src/training/smart_data_merger.py)
- **Preprocessing**: [`src.preprocess.preprocess`](src/preprocess/preprocess.py)
- **Model Training**: [`src.train_model`](src/train_model.py)
- **Threshold Tuning**: [`src.tune_threshold`](src/tune_threshold.py)
- **Prediction**: [`src.predict`](src/predict.py)
- **Monitoring**: [`src.monitor.monitor`](src/monitor/monitor.py)
- **Notification**: [`src.monitor.notification`](src/monitor/notification.py)

## 📊 Dashboard & API

- Real-time stats, performance, and health endpoints via Flask.
- WebSocket events for live dashboard updates.

## 🛡️ Monitoring & Alerts

- Model drift detection and alerting via email/Slack.
- Performance tracking and auto-retirement of old models.

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License

---
