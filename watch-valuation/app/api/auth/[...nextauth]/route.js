import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import bcrypt from 'bcryptjs';

// In-memory user store (replace with database in production)
const users = [
  {
    id: '1',
    email: 'demo@lapometro.com',
    password: '$2a$10$YourHashedPasswordHere', // 'demo123'
    name: 'Usuario Demo'
  }
];

// Hash the demo password for testing
const hashPassword = async (password) => {
  return await bcrypt.hash(password, 10);
};

// For demo: create a demo user with password 'demo123'
(async () => {
  const hashedPassword = await bcrypt.hash('demo123', 10);
  users[0].password = hashedPassword;
})();

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: "Email", type: "email", placeholder: "tu@email.com" },
        password: { label: "Contraseña", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Por favor ingresa email y contraseña');
        }

        // Find user
        const user = users.find(u => u.email === credentials.email);

        if (!user) {
          throw new Error('No se encontró el usuario');
        }

        // Check password
        const isValidPassword = await bcrypt.compare(
          credentials.password,
          user.password
        );

        if (!isValidPassword) {
          throw new Error('Contraseña incorrecta');
        }

        return {
          id: user.id,
          email: user.email,
          name: user.name
        };
      }
    })
  ],
  pages: {
    signIn: '/auth/signin',
  },
  session: {
    strategy: 'jwt',
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET || 'your-secret-key-here-change-in-production',
});

export { handler as GET, handler as POST };
