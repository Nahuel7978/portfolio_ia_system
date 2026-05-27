package portfolio_spring.v1.dto;

public class PublicEntryDetailDTO {
    private KnowledgeEntryDTO entry;
    private String summaryMarkdown;
    private Integer summaryDocumentId;
	public KnowledgeEntryDTO getEntry() {
		return entry;
	}
	public void setEntry(KnowledgeEntryDTO entry) {
		this.entry = entry;
	}
	public String getSummaryMarkdown() {
		return summaryMarkdown;
	}
	public void setSummaryMarkdown(String summaryMarkdown) {
		this.summaryMarkdown = summaryMarkdown;
	}
	public Integer getSummaryDocumentId() {
		return summaryDocumentId;
	}
	public void setSummaryDocumentId(Integer summaryDocumentId) {
		this.summaryDocumentId = summaryDocumentId;
	}



}
