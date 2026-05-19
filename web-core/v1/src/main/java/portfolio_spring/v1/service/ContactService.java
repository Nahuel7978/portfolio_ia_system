package portfolio_spring.v1.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import portfolio_spring.v1.dto.ContactRequestDTO;
import portfolio_spring.v1.model.ContactMessage;
import portfolio_spring.v1.repository.ContactMessageRepository;

@Service
public class ContactService {

    private final ContactMessageRepository repository;
    private final JavaMailSender mailSender;

    @Value("${spring.mail.username}")
    private String destinationEmail; // Te lo envías a ti mismo

    public ContactService(ContactMessageRepository repository, JavaMailSender mailSender) {
        this.repository = repository;
        this.mailSender = mailSender;
    }

    @Transactional
    public void processContactRequest(ContactRequestDTO dto) {
        // 1. Guardar en BD
        ContactMessage msg = new ContactMessage();
        msg.setName(dto.getName());
        msg.setEmail(dto.getEmail());
        msg.setSubject(dto.getSubject());
        msg.setMessage(dto.getMessage());
        msg.setStatus("UNREAD");
        repository.save(msg);

        // 2. Disparar el email en segundo plano
        sendEmailNotification(dto);
    }

    @Async
    protected void sendEmailNotification(ContactRequestDTO dto) {
        try {
            SimpleMailMessage mailMessage = new SimpleMailMessage();
            mailMessage.setTo(destinationEmail);
            mailMessage.setSubject("Nuevo Contacto Portfolio: " + dto.getSubject());
            mailMessage.setText(
                "Has recibido un nuevo mensaje desde tu Portfolio:\n\n" +
                "Nombre: " + dto.getName() + "\n" +
                "Email: " + dto.getEmail() + "\n\n" +
                "Mensaje:\n" + dto.getMessage()
            );
            mailSender.send(mailMessage);
            System.out.println("✅ Email enviado con éxito sobre el asunto: " + dto.getSubject());
        } catch (Exception e) {
            // El usuario no verá este error, pero queda en los logs
            System.err.println("❌ Error enviando el email: " + e.getMessage());
        }
    }
}
