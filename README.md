# MiikaMods - acesso

Este conteudo vai na raiz de `Killuawaore/MiikaMods`.

Depois da configuracao inicial, voce edita somente `access/usuarios.txt` pelo proprio GitHub.
Coloque um nick Minecraft por linha e salve com **Commit changes**. O GitHub Action resolve os nicks para UUID, assina a lista e atualiza `access/manifest.json` automaticamente.

A Action tambem renova o manifesto no primeiro dia de cada mes. Os mods usam o UUID da conta. Um cache assinado que ja foi validado continua funcionando sem limite de tempo se o GitHub estiver indisponivel. Quando uma verificacao mensal consegue acessar o GitHub de novo, qualquer remocao passa a valer.

## Configuracao unica

1. No repositorio `Killuawaore/MiikaMods`, abra **Settings -> Secrets and variables -> Actions**.
2. Crie um **Repository secret** chamado `RUNTIME_PROFILE_KEY`.
3. Cole nele a chave privada fornecida separadamente. Ela nunca vai dentro do repositorio ou dos JARs.
4. Coloque esta pasta na raiz do repositorio.
5. Edite `access/usuarios.txt` e coloque seu nick Minecraft e os nicks autorizados.
6. Abra **Actions -> Publicar acesso -> Run workflow** uma vez, ou apenas salve `access/usuarios.txt` depois que o Secret existir.

A fonte oficial usada pelos mods e:
`https://raw.githubusercontent.com/Killuawaore/MiikaMods/main/access/manifest.json`

`access/public-key.txt` pode ser publico. A chave privada nao pode ser publicada.
