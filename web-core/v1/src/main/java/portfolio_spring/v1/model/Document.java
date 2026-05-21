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

    // Carga perezosa estricta para evitar OutOfMemory
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
}
