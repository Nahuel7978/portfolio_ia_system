package portfolio_spring.v1.model;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import java.io.Serializable;
import java.util.Objects;

@Embeddable
public class KnowledgeEntryTechnologyId implements Serializable {

    @Column(name = "entry_id")
    private Integer entryId;

    @Column(name = "technology_id")
    private Integer technologyId;

    public KnowledgeEntryTechnologyId() {}

    public KnowledgeEntryTechnologyId(Integer entryId, Integer technologyId) {
        this.entryId = entryId;
        this.technologyId = technologyId;
    }

    // Getters y Setters
    public Integer getEntryId() { return entryId; }
    public void setEntryId(Integer entryId) { this.entryId = entryId; }
    public Integer getTechnologyId() { return technologyId; }
    public void setTechnologyId(Integer technologyId) { this.technologyId = technologyId; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        KnowledgeEntryTechnologyId that = (KnowledgeEntryTechnologyId) o;
        return Objects.equals(entryId, that.entryId) && Objects.equals(technologyId, that.technologyId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(entryId, technologyId);
    }
}
