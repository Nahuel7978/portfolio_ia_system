package portfolio_spring.v1.model;

import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;
import jakarta.persistence.Basic;
import jakarta.persistence.FetchType;
import jakarta.persistence.Lob;
import org.hibernate.annotations.JdbcTypeCode;

@Entity
@Table(name = "knowledge_entries")
public class KnowledgeEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false)
    private String name;

    @Lob
    @Basic(fetch = FetchType.LAZY)
    @JdbcTypeCode(java.sql.Types.BINARY)
    @Column(name = "image_data")
    private byte[] imageData;

    @Column(name = "image_mime_type")
    private String imageMimeType;

    @Column(nullable = false)
    private String area;

    @Column(name = "area_secondary")
    private String areaSecondary;

    @Column(nullable = false)
    private String status;

    @OneToMany(mappedBy = "knowledgeEntry", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<KnowledgeEntryTechnology> entryTechnologies = new ArrayList<>();

    // Método utilitario para mantener sincronización bidireccional (Buenas Prácticas JPA)
    public void addTechnology(Technology technology, String role) {
        KnowledgeEntryTechnology ket = new KnowledgeEntryTechnology();
        ket.setKnowledgeEntry(this);
        ket.setTechnology(technology);
        ket.setRole(role);
        entryTechnologies.add(ket);
    }

    // Getters y Setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public byte[] getImageData() {return imageData;}

	public void setImageData(byte[] imageData) {this.imageData = imageData;}
	public String getImageMimeType() {return imageMimeType;}
	public void setImageMimeType(String imageMimeType) {this.imageMimeType = imageMimeType;}
	public String getArea() { return area; }
    public void setArea(String area) { this.area = area; }
    public String getAreaSecondary() { return areaSecondary; }
    public void setAreaSecondary(String areaSecondary) { this.areaSecondary = areaSecondary; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public List<KnowledgeEntryTechnology> getEntryTechnologies() { return entryTechnologies; }
    public void setEntryTechnologies(List<KnowledgeEntryTechnology> entryTechnologies) { this.entryTechnologies = entryTechnologies; }
}
