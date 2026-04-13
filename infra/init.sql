-- Workshop database schema and seed data

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100)
);

CREATE TABLE sessions (
    token UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '4 hours'
);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id, created_at);
CREATE INDEX idx_sessions_token ON sessions(token);

-- Seed 30 participant accounts (password: techday2026)
INSERT INTO users (username, password_hash, display_name) VALUES
('participant01', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 1'),
('participant02', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 2'),
('participant03', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 3'),
('participant04', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 4'),
('participant05', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 5'),
('participant06', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 6'),
('participant07', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 7'),
('participant08', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 8'),
('participant09', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 9'),
('participant10', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 10'),
('participant11', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 11'),
('participant12', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 12'),
('participant13', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 13'),
('participant14', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 14'),
('participant15', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 15'),
('participant16', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 16'),
('participant17', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 17'),
('participant18', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 18'),
('participant19', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 19'),
('participant20', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 20'),
('participant21', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 21'),
('participant22', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 22'),
('participant23', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 23'),
('participant24', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 24'),
('participant25', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 25'),
('participant26', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 26'),
('participant27', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 27'),
('participant28', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 28'),
('participant29', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 29'),
('participant30', '$2b$12$YOwQaOKS0mU1CW.Fd3fEl.stdiqIJjybsQeAqF.Rh4yH2OpVe5J32', 'Participant 30');
