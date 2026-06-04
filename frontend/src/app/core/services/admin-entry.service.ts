import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment.development';

@Injectable({
  providedIn: 'root'
})
export class AdminEntryService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  getProjects(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/public/knowledge-entries/projects`);
  }

  getBlogs(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/public/knowledge-entries/blogs`);
  }

  deleteEntry(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/admin/knowledge-entries/${id}`);
  }

  createEntry(formData: FormData): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/admin/knowledge-entries`, formData);
  }

  uploadDocument(entryId: number, documentData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/knowledge-entries/${entryId}/documents`, documentData, { responseType: 'text' });
  }

  // Actualizar datos de la entrada (JSON)
  updateEntry(id: number, data: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/admin/knowledge-entries/${id}`, data);
  }

  // Actualizar imagen de portada separadamente
  updateCoverImage(id: number, image: File): Observable<any> {
    const formData = new FormData();
    formData.append('image', image);
    return this.http.put(`${this.apiUrl}/admin/knowledge-entries/${id}/image`, formData);
  }

  // Obtener documentos existentes (metadatos)
  getEntryDocuments(id: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/admin/knowledge-entries/${id}/documents`);
  }

  getEntryById(id: Number): Observable<any> {
    // Retorna el PublicEntryDetailDTO que definimos en el backend
    return this.http.get<any>(`${this.apiUrl}/public/knowledge-entries/${id}`);
  }

  // Borrar un documento específico
  deleteDocument(documentId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/admin/knowledge-entries/documents/${documentId}`);
  }

  // Descargar documento (Forzamos responseType a 'blob')
  downloadDocument(documentId: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/admin/knowledge-entries/documents/${documentId}/download`, {
      responseType: 'blob'
    });
  }
}

///Object { headers: {…}, status: 400, statusText: "Unknown Error", url: "http://localhost:8080/api/v1/admin/knowledge-entries/9", ok: false, type: undefined, r