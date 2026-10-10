"""Streamlit dashboard for the AI/NLP Risk Engine prototype."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from risk_engine.schema import NormalizedRecord
from risk_engine.analyzer import analyze_record
from downstream.stress_test import run_stress_test

ROOT = Path(__file__).resolve().parent
SAMPLE_SIGNALS = ROOT / "data" / "sample" / "risk_signals.json"

st.set_page_config(page_title="AI/NLP Risk Engine", page_icon="📊", layout="wide")
st.title("AI/NLP Risk Engine")
st.caption("Explainable prototype • rule-based baseline • illustrative portfolio scenarios")
st.warning(
    "Prototype only: sentiment and event labels use keyword rules; impact is a heuristic, "
    "and portfolio shocks are illustrative assumptions—not calibrated forecasts or investment advice."
)

tab_analyze, tab_stress, tab_history, tab_about = st.tabs(
    ["Analyze text", "Portfolio stress test", "Sample signals", "Method & limitations"]
)

with tab_analyze:
    st.subheader("Analyze a financial headline or social post")
    with st.form("analyze_form"):
        text = st.text_area(
            "Text to analyze",
            value="Acme Bank faces a credit downgrade after reporting liquidity concerns and losses.",
            height=110,
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            source = st.selectbox("Source type", ["manual_demo", "gdelt", "financial_tweets", "newsapi"])
        with col2:
            source_id = st.text_input("Source record ID (optional)", value="")
        with col3:
            ticker = st.text_input("Ticker (optional)", value="")
        company = st.text_input("Company name (optional)", value="")
        submitted = st.form_submit_button("Analyze text", type="primary")

    if submitted:
        if not text.strip():
            st.error("Enter some text before analyzing.")
        else:
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            record = NormalizedRecord(
                record_id=f"manual_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}",
                source=source,
                published_at=now,
                text=text.strip(),
                source_id=source_id.strip() or None,
                metadata={"company": company.strip() or None, "ticker": ticker.strip() or None},
            )
            try:
                signal = analyze_record(record).to_dict()
                st.session_state["latest_signal"] = signal
                st.success("Risk signal generated.")
            except (ValueError, TypeError) as exc:
                st.error(f"Could not analyze this record: {exc}")

    signal = st.session_state.get("latest_signal")
    if signal:
        st.markdown("### Generated risk signal")
        sentiment = signal["sentiment"]
        event = signal["event"]
        impact = signal["impact"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sentiment", sentiment["label"].title(), f'{sentiment["score"]:+.3f}')
        c2.metric("Event type", event["type"].replace("_", " ").title())
        c3.metric("Impact score", f'{impact["score"]}/10')
        c4.metric("Heuristic confidence", f'{event["confidence"]:.0%}', help="Evidence indicator, not a calibrated probability.")
        st.markdown("**Evidence / input text**")
        st.write(signal["evidence"]["text_span"])
        st.markdown("**Matched sentiment phrases**")
        st.write(", ".join(signal["evidence"].get("matched_sentiment_phrases", [])) or "No sentiment phrases matched.")
        st.markdown("**Entities (heuristic extraction)**")
        st.json(signal["entities"])
        with st.expander("Inspect complete machine-readable RiskSignal JSON"):
            st.json(signal)
        st.download_button(
            "Download this RiskSignal as JSON",
            data=json.dumps(signal, indent=2, ensure_ascii=False),
            file_name=f'{signal["signal_id"]}.json',
            mime="application/json",
        )

with tab_stress:
    st.subheader("Stress-test the synthetic portfolio")
    st.write("Uses the project's existing `run_stress_test()` function and its documented illustrative sector shocks.")
    latest = st.session_state.get("latest_signal")
    use_latest = st.checkbox("Include the headline analyzed in the first tab", value=bool(latest), disabled=not bool(latest))
    uploaded_signals = st.file_uploader("Or upload a JSON file containing a list of RiskSignals", type=["json"], key="stress_upload")
    signals = []
    if use_latest and latest:
        signals.append(latest)
    if uploaded_signals is not None:
        try:
            parsed = json.loads(uploaded_signals.getvalue().decode("utf-8"))
            if not isinstance(parsed, list):
                raise ValueError("Expected a JSON array of RiskSignals.")
            signals.extend(parsed)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            st.error(f"Could not read uploaded signals: {exc}")
    if st.button("Run stress test", type="primary", key="run_stress"):
        if not signals:
            st.info("Analyze a headline or upload a RiskSignal JSON array first.")
        else:
            try:
                result = run_stress_test(signals)
                st.session_state["stress_result"] = result
            except (ValueError, TypeError, KeyError) as exc:
                st.error(f"Stress test failed: {exc}")

    result = st.session_state.get("stress_result")
    if result:
        st.metric("Synthetic portfolio baseline", f'{result["portfolio_before"]:,.0f} {result["currency"]}')
        rows = []
        for scenario in result["scenarios"]:
            rows.append({
                "Event": scenario["event_type"],
                "Impact": scenario["impact_score"],
                "Change (%)": scenario["change_pct"],
                "Change (units)": scenario["absolute_change"],
                "Mapping": scenario["mapping_status"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        choices = [f'{i + 1}. {s["event_type"]} — impact {s["impact_score"]}' for i, s in enumerate(result["scenarios"])]
        selected = st.selectbox("Inspect scenario", range(len(choices)), format_func=lambda i: choices[i])
        scenario = result["scenarios"][selected]
        st.caption(scenario["assumption"])
        st.dataframe(pd.DataFrame(scenario["holdings"]), use_container_width=True, hide_index=True)
        with st.expander("Inspect complete stress-test JSON"):
            st.json(result)
        st.download_button(
            "Download stress-test results",
            data=json.dumps(result, indent=2),
            file_name="stress_test_results.json",
            mime="application/json",
        )

with tab_history:
    st.subheader("Bundled sample signals")
    st.caption("This view intentionally loads the small bundled synthetic demo, not the 28k-row local historical output.")
    if SAMPLE_SIGNALS.exists():
        try:
            sample = json.loads(SAMPLE_SIGNALS.read_text(encoding="utf-8"))
            if isinstance(sample, list) and sample:
                rows = [{
                    "Signal ID": s.get("signal_id"),
                    "Source": (s.get("source") or {}).get("type"),
                    "Event": (s.get("event") or {}).get("type"),
                    "Sentiment": (s.get("sentiment") or {}).get("label"),
                    "Sentiment score": (s.get("sentiment") or {}).get("score"),
                    "Impact": (s.get("impact") or {}).get("score"),
                    "Timestamp": s.get("timestamp"),
                } for s in sample]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.download_button(
                    "Download bundled sample signals",
                    data=json.dumps(sample, indent=2, ensure_ascii=False),
                    file_name="risk_signals.json",
                    mime="application/json",
                )
            else:
                st.info("Sample signal file exists but does not contain a non-empty JSON array. Run `python run_demo.py`.")
        except (OSError, json.JSONDecodeError) as exc:
            st.error(f"Could not load sample signals: {exc}")
    else:
        st.info("Sample output not found. Run `python run_demo.py` from the repository root, then refresh this page.")

with tab_about:
    st.subheader("How this prototype works")
    st.markdown(
        """
        1. **Normalize:** source adapters map incoming text and metadata into a common record contract.
        2. **Analyze:** the current baseline matches phrase lexicons and event-taxonomy keywords.
        3. **Score impact:** a documented weighted heuristic combines event severity, consequence, scope,
           entity relevance and sentiment magnitude.
        4. **Validate and expose:** a structured `RiskSignal` is shown and can be exported as JSON.
        5. **Stress-test:** event type and impact scale illustrative sector shocks for a synthetic portfolio.
        """
    )
    st.markdown("**Important limitations**")
    st.markdown(
        "- The analyzer is deterministic and rule-based, not a trained financial NLP model.\n"
        "- Entity extraction can produce false positives; manually verify entities and classifications.\n"
        "- Confidence fields are heuristic evidence indicators, not calibrated probabilities.\n"
        "- Stress scenarios are assumptions, not empirical estimates, financial advice, or trading signals.\n"
        "- Historical CSV analysis is available through the existing CLI; this dashboard does not automatically load the large local output."
    )
    st.markdown("**Reproduce the baseline demo**")
    st.code("python -m unittest discover -s tests -v\npython run_demo.py", language="powershell")
