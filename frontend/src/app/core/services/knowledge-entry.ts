import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment.development';
import { KnowledgeEntryDTO } from '../models/knowledge-entry.interface';

@Injectable({ providedIn: 'root' })
export class KnowledgeEntryService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/public/knowledge-entries`;

  getProjects(): Observable<KnowledgeEntryDTO[]> {
    return this.http.get<KnowledgeEntryDTO[]>(`${this.apiUrl}/projects`);
  }

  getBlogs(): Observable<KnowledgeEntryDTO[]> {
    return this.http.get<KnowledgeEntryDTO[]>(`${this.apiUrl}/blogs`);
  }

  getEntryById(id: Number): Observable<any> {
    // Retorna el PublicEntryDetailDTO que definimos en el backend
    return this.http.get<any>(`${this.apiUrl}/${id}`);
  }

}