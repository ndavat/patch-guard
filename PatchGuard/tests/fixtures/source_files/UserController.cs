using System;
using System.Data;
using System.Data.SqlClient;
using Microsoft.AspNetCore.Mvc;

namespace MyApp.Controllers
{
    public class UserController : Controller
    {
        private readonly string _connectionString;

        public UserController(string connectionString)
        {
            _connectionString = connectionString;
        }

        public IActionResult GetUser(string userId)
        {
            using (var connection = new SqlConnection(_connectionString))
            {
                connection.Open();

                // SQL Injection vulnerability on line 42
                var query = "SELECT * FROM Users WHERE UserId = '" + userId + "'";
                var command = new SqlCommand(query, connection);

                var reader = command.ExecuteReader();

                if (reader.Read())
                {
                    var user = new
                    {
                        Id = reader["UserId"],
                        Name = reader["UserName"],
                        Email = reader["Email"]
                    };
                    return Ok(user);
                }

                return NotFound();
            }
        }

        public IActionResult UpdateUser(string userId, string newName)
        {
            using (var connection = new SqlConnection(_connectionString))
            {
                connection.Open();
                var query = $"UPDATE Users SET UserName = '{newName}' WHERE UserId = '{userId}'";
                var command = new SqlCommand(query, connection);
                command.ExecuteNonQuery();
                return Ok();
            }
        }
    }
}
