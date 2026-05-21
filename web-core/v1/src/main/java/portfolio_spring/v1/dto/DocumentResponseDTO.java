package portfolio_spring.v1.dto;

public class DocumentResponseDTO {
    private Integer id;
    private Integer entryId;
    private String documentName;
    private String docType;
    private String mimeType;
    private Integer technicalDepth;
    private String language;
    private Integer importance;
    private String syncStatus;

	public Integer getId() {
		return id;
	}
	public void setId(Integer id) {
		this.id = id;
	}
	public Integer getEntryId() {
		return entryId;
	}
	public void setEntryId(Integer entryId) {
		this.entryId = entryId;
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

    // TODO: Generar Getters y Setters

}
