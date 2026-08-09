import ChatWidget from "@/components/ChatWidget";
import PDFUploader from "@/components/PDFUploader";

const styles = {
  page: {
    width: "100%",
    maxWidth: "1320px",
    margin: "0 auto",
    padding: "3rem 1.5rem 4rem",
    display: "flex",
    flexDirection: "column" as const,
    gap: "2rem",
  },
  hero: {
    padding: "2rem",
    borderRadius: "28px",
    background: "rgba(219, 234, 254, 0.9)",
    border: "1px solid rgba(59, 130, 246, 0.24)",
    boxShadow: "0 18px 48px rgba(15, 23, 42, 0.08)",
    display: "grid",
    gap: "1.5rem",
  },
  eyebrow: {
    color: "#1d4ed8",
    fontWeight: 700,
    letterSpacing: "0.18em",
    textTransform: "uppercase",
    margin: 0,
    fontSize: "0.85rem",
  },
  title: {
    margin: "0.75rem 0 0",
    fontSize: "clamp(2.4rem, 4vw, 4.2rem)",
    lineHeight: 1.02,
    color: "#0f172a",
  },
  subtitle: {
    margin: "1.2rem 0 0",
    maxWidth: "720px",
    fontSize: "1rem",
    lineHeight: 1.8,
    color: "#334155",
  },
  panelGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(12, minmax(0, 1fr))",
    gap: "1.5rem",
  },
  leftPanel: {
    gridColumn: "span 3",
  },
  rightPanel: {
    gridColumn: "span 9",
  },
  cardShell: {
    width: "100%",
    borderRadius: "24px",
    background: "rgba(255, 255, 255, 0.92)",
    border: "1px solid rgba(148, 163, 184, 0.18)",
    boxShadow: "0 10px 36px rgba(15, 23, 42, 0.06)",
    overflow: "hidden",
    minHeight: "520px",
  },
  cardHeader: {
    background: "linear-gradient(135deg, #bfdbfe 0%, #93c5fd 100%)",
    padding: "1.3rem 1.5rem",
    color: "#0f172a",
  },
  cardTitle: {
    margin: 0,
    fontSize: "1.15rem",
    fontWeight: 700,
  },
  cardBody: {
    padding: "1.5rem",
  },
};

export default function Home() {
  return (
    <main style={styles.page}>
      <section style={styles.hero}>
        <div>
          <p style={styles.eyebrow}>Professor DOTU</p>
          <h1 style={styles.title}>A smarter study zone for your textbook questions.</h1>
          <p style={styles.subtitle}>
            Upload your PDF and use the chat tutor to explore concepts, get answers, and review sources instantly.
          </p>
        </div>
      </section>

      <section style={styles.panelGrid}>
        <div style={{ ...styles.leftPanel, minWidth: 0 }}>
          <div style={styles.cardShell}>
            <div style={styles.cardHeader}>
              <h2 style={styles.cardTitle}>Textbook upload</h2>
            </div>
            <div style={styles.cardBody}>
              <PDFUploader />
            </div>
          </div>
        </div>
        <div style={{ ...styles.rightPanel, minWidth: 0 }}>
          <div style={styles.cardShell}>
            <div style={styles.cardHeader}>
              <h2 style={styles.cardTitle}>Chat with Professor DOTU</h2>
            </div>
            <div style={styles.cardBody}>
              <ChatWidget />
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
