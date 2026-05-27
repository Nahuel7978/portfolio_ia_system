package portfolio_spring.v1.model;

import jakarta.persistence.*;

@Entity
@Table(name = "knowledge_entry_technologies")
public class KnowledgeEntryTechnology {

    @EmbeddedId
    private KnowledgeEntryTechnologyId id = new KnowledgeEntryTechnologyId();

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("entryId")
    @JoinColumn(name = "entry_id")
    private KnowledgeEntry knowledgeEntry;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("technologyId")
    @JoinColumn(name = "technology_id")
    private Technology technology;

    @Column(nullable = false)
    private String role; // 'primary' o 'secondary'

    // Getters y Setters
    public KnowledgeEntryTechnologyId getId() { return id; }
    public void setId(KnowledgeEntryTechnologyId id) { this.id = id; }
    public KnowledgeEntry getKnowledgeEntry() { return knowledgeEntry; }
    public void setKnowledgeEntry(KnowledgeEntry knowledgeEntry) { this.knowledgeEntry = knowledgeEntry; }
    public Technology getTechnology() { return technology; }
    public void setTechnology(Technology technology) { this.technology = technology; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
	public void setEntry(KnowledgeEntry ke) { this.knowledgeEntry = ke; }
}
