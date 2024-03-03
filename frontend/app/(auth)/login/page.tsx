
export default function login() {
  // TODO: Add CSRF tag
  return (
    <main>
      <div>
        <form method="post">
          <label htmlFor="username">Username:</label><br/>
          <input type="text" id="username" name="username" /><br/>
          <label htmlFor="password">Password:</label><br/>
          <input type="password" id="password" name="password" /><br/>
          <input type="submit" value="Login" />
        </form>
      </div>
    </main>
  );
}