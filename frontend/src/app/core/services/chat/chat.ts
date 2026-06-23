import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, catchError, throwError, tap, lastValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface ChatMessage {
  sender: 'user' | 'agent';
  text: string;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = environment.iaApiUrl;
  private readonly TOKEN_KEY = 'chat_session_token';

  // Estado reactivo para los mensajes
  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  constructor(private http: HttpClient) {
    // Si ya existe un token, podríamos cargar un saludo inicial diferente,
    // o simplemente mantener el arreglo vacío hasta que el usuario escriba.
    this.messagesSubject.next([{ sender: 'agent', text: "Hi! I'm Nahuel's virtual assistant. How can I help you today? You can write to me in any language you like." }]);
  }

  // 1. Obtener o recuperar el Token
  public async ensureToken(): Promise<string> {
    let token = localStorage.getItem(this.TOKEN_KEY);
    if (!token) {
      try {
        const response: any = await this.http.get(`${this.apiUrl}/auth/chat-token`).toPromise();
        token = response.access_token;
        if(token) localStorage.setItem(this.TOKEN_KEY, token);
      } catch (error) {
        console.error('Error obteniendo token de chat:', error);
        throw error;
      }
    }
    return token || '';
  }

  // 2. Enviar Mensaje
  public async sendMessage(message: string): Promise<void> {
    // Agregamos el mensaje del usuario a la UI inmediatamente
    const currentMessages = this.messagesSubject.getValue();
    this.messagesSubject.next([...currentMessages, { sender: 'user', text: message }]);

    try {
      const token = await this.ensureToken();
      const headers = new HttpHeaders({
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      });

      const payload = { message: message };

      const response: any = await lastValueFrom(this.http.post(`${this.apiUrl}/chat`, payload, { headers }));
      
      // Agregamos la respuesta del agente
      this.messagesSubject.next([...this.messagesSubject.getValue(), { sender: 'agent', text: response.answer }]);

    } catch (error) {
      this.handleChatError(error);
    }
  }

  private handleChatError(error: any) {
    let errorMsg = 'Sorry, there was a connection error.';
    if (error instanceof HttpErrorResponse) {
        if (error.status === 429) {
            errorMsg = 'You have reached the message limit for now. Please try again in a few minutes.';
        } else if (error.status === 401) {
            // Token expirado, lo borramos para que el próximo ensureToken genere uno nuevo
            localStorage.removeItem(this.TOKEN_KEY);
            errorMsg = 'Your session has expired. Please try sending your message again to reconnect.';
        }
    }
    this.messagesSubject.next([...this.messagesSubject.getValue(), { sender: 'agent', text: errorMsg }]);
  }
}