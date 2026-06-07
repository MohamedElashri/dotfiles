# ~/.zshenv is read by every zsh process, including scripts.
# Keep it minimal and avoid sourcing interactive or tool-generated files here.
case ":$PATH:" in
  *:"$HOME/.cargo/bin":*) ;;
  *) export PATH="$HOME/.cargo/bin:$PATH" ;;
esac
