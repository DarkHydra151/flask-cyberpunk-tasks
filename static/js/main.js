document.addEventListener('DOMContentLoaded', function() {
    
    document.querySelectorAll('.task-toggle').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const taskItem = this.closest('.cyber-task-item');
            const taskId = taskItem.dataset.id;
            
            fetch(`/api/task/${taskId}/toggle`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    taskItem.classList.toggle('completed', data.is_completed);
                }
            });
        });
    });

    document.querySelectorAll('.task-delete').forEach(button => {
        button.addEventListener('click', function() {
            if(!confirm('Підтвердити видалення протоколу?')) return;
            
            const taskItem = this.closest('.cyber-task-item');
            const taskId = taskItem.dataset.id;

            fetch(`/api/task/${taskId}/delete`, {
                 method: 'DELETE',
                 headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'deleted') {
                    taskItem.style.opacity = '0';
                    setTimeout(() => taskItem.remove(), 300);
                }
            });
        });
    });

    const searchInput = document.getElementById('taskSearch');
    if(searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.cyber-task-item').forEach(item => {
                const title = item.querySelector('.task-title').textContent.toLowerCase();
                if(title.includes(term)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    setTimeout(() => {
        document.querySelectorAll('.cyber-alert').forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000); 
});

function editTaskDesc(id, oldTitle) {
    const newTitle = prompt("Нова назва завдання:", oldTitle);
    if (newTitle && newTitle !== oldTitle) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/tasks'; 
        
        fetch(`/api/task/${id}/update_text`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title: newTitle})
        }).then(() => location.reload());
    }
}


function openEditModal(button) {
    const id = button.getAttribute('data-id');
    const title = button.getAttribute('data-title');
    const desc = button.getAttribute('data-desc');
    const priority = button.getAttribute('data-priority');
    const date = button.getAttribute('data-date');

    const form = document.getElementById('editTaskForm');
    form.action = `/task/${id}/edit`;

    document.getElementById('editTitle').value = title;
    document.getElementById('editDesc').value = desc;
    document.getElementById('editPriority').value = priority;
    document.getElementById('editDate').value = date;
}