-- 1. Tablas Base
CREATE TABLE technologies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL CHECK (category IN ('language', 'framework', 'library', 'tool', 'algorithm', 'infrastructure', 'platform'))
);

CREATE TABLE knowledge_entries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    area VARCHAR(50) NOT NULL CHECK (area IN ('AI', 'ML', 'Robotics', 'NLP', 'Web', 'Programming', 'Computer Vision', 'Data Analytics', 'Education', 'Activity', 'Languages', 'Blog')),
    area_secondary VARCHAR(50) CHECK (area_secondary IN ('AI', 'ML', 'Robotics', 'NLP', 'Web', 'Programming', 'Computer Vision', 'Data Analytics', 'Education', 'Activity', 'Languages', 'Blog')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'completed')),
    image_data BYTEA,
    image_mime_type VARCHAR(100)
);

CREATE TABLE knowledge_entry_technologies (
    entry_id INTEGER NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    technology_id INTEGER NOT NULL REFERENCES technologies(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('primary', 'secondary')),
    PRIMARY KEY (entry_id, technology_id)
);

-- 2. Tabla de Documentos Refactorizada
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    document_name VARCHAR(255) NOT NULL,
    doc_type VARCHAR(50) NOT NULL CHECK (doc_type IN ('summary', 'technical_report', 'design_decisions', 'dev_report', 'academic_record', 'work_experience', 'extracurricular')),
    technical_depth INTEGER NOT NULL CHECK (technical_depth BETWEEN 1 AND 5),
    language VARCHAR(2) NOT NULL CHECK (language IN ('es', 'en')),
    importance INTEGER NOT NULL CHECK (importance BETWEEN 1 AND 5),
    file_data BYTEA,
    mime_type VARCHAR(100),
    sync_status VARCHAR(20) DEFAULT 'PENDING' CHECK (sync_status IN ('PENDING', 'SYNCED', 'FAILED'))
);

-- 3. Entidades de Seguridad y Contacto
CREATE TABLE administrators (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE contact_messages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'UNREAD' CHECK (status IN ('UNREAD', 'READ', 'REPLIED'))
);
