package portfolio_spring.v1.model;

import org.hibernate.annotations.JdbcTypeCode;

import jakarta.persistence.*;

@Entity
@Table(name = "documents")
public class Document {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    // Relación ManyToOne con KnowledgeEntry
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "entry_id", nullable = false)
    private KnowledgeEntry entry;

    @Column(name = "document_name", nullable = false)
    private String documentName;

    @Column(name = "doc_type", nullable = false)
    private String docType;

    @Lob
    @Basic(fetch = FetchType.LAZY)
    @JdbcTypeCode(java.sql.Types.BINARY)
    @Column(name = "file_data", nullable = false)
    private byte[] fileData;

    @Column(name = "mime_type", nullable = false)
    private String mimeType;

    @Column(name = "technical_depth", nullable = false)
    private Integer technicalDepth;

    @Column(name = "language", nullable = false)
    private String language;

    @Column(name = "importance", nullable = false)
    private Integer importance;

    @Column(name = "sync_status", nullable = false)
    private String syncStatus = "PENDING"; // Estado por defecto

    // TODO: Generar Getters y Setters
	public Integer getId() {
		return id;
	}

	public void setId(Integer id) {
		this.id = id;
	}

	public KnowledgeEntry getEntry() {
		return entry;
	}

	public void setEntry(KnowledgeEntry entry) {
		this.entry = entry;
	}

	public String getDocumentName() {
		return documentName;
	}

	public void setDocumentName(String documentName) {
		this.documentName = documentName;
	}

	public String getDocType() {
		return docType;
	}

	public void setDocType(String docType) {
		this.docType = docType;
	}

	public byte[] getFileData() {
		return fileData;
	}

	public void setFileData(byte[] fileData) {
		this.fileData = fileData;
	}

	public String getMimeType() {
		return mimeType;
	}

	public void setMimeType(String mimeType) {
		this.mimeType = mimeType;
	}

	public Integer getTechnicalDepth() {
		return technicalDepth;
	}

	public void setTechnicalDepth(Integer technicalDepth) {
		this.technicalDepth = technicalDepth;
	}

	public String getLanguage() {
		return language;
	}

	public void setLanguage(String language) {
		this.language = language;
	}

	public Integer getImportance() {
		return importance;
	}

	public void setImportance(Integer importance) {
		this.importance = importance;
	}

	public String getSyncStatus() {
		return syncStatus;
	}

	public void setSyncStatus(String syncStatus) {
		this.syncStatus = syncStatus;
	}

}
